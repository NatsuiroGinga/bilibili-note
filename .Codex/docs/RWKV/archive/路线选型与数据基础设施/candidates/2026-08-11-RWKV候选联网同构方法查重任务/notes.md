# 研究记录：RWKV 候选 A—D 联网同构方法查重

## 固定证据边界

- 全文证据只支撑机制来源、相似度、原创表述边界与实验设计依据。
- 官方源码只证明公开实现范围，不能替代论文方法与实验结论。
- 摘要与元数据只用于候选筛选和访问阻塞清单，不能支撑公式、消融、局限或“强同构”结论。
- 所有候选仍为“未筛选／实验待证”；本记录不推断 LSPR23→LSPR24 的实际效果。

## 查询式日志

检索日期均为 2026-08-11；来源限定为原论文、会议／期刊官网、arXiv、作者页与官方源码。

1. `site:arxiv.org 2023 2024 2025 RWKV network intrusion detection anomaly detection time series RWKV-7`
2. `site:arxiv.org 2023 2024 2025 network intrusion detection concept drift cross-year temporal distribution shift`
3. `site:arxiv.org 2023 2024 2025 test-time adaptation anomaly detection trusted memory normal prototype contamination`
4. `site:arxiv.org 2023 2024 2025 generalized delta rule state space model distribution shift time series`
5. `site:arxiv.org 2023 2024 2025 continuous-time state space model irregularly sampled time series Mamba`
6. `site:arxiv.org 2023 2024 2025 frequency-domain state space model time series anomaly detection Mamba Fourier`
7. `site:proceedings.mlr.press 2023 2024 time series out-of-distribution generalization invariant learning environment robustness`
8. `site:arxiv.org 2023 2024 2025 suffix automaton sequence model anomaly detection vector quantization residual`
9. `continuous-time Mamba irregular time series arxiv`
10. `continuous time state space model irregularly sampled time series 2024 arxiv selective state space`
11. `irregular time series Mamba continuous decay exp delta t state space model paper`
12. `site:openreview.net continuous time Mamba irregular time series`
13. `"time-aware" Mamba irregular time series paper 2024`
14. `"timespan" Mamba irregular sampling state space paper`
15. `"delta t" Mamba irregular time series arxiv 2025`
16. `"exponential decay" Mamba irregular time series state space`
17. `channel-independent masked pretraining dynamic graph multivariate time series 2023 paper`
18. `masked time series pretraining channel independent graph neural network 2024`
19. `multivariate time series channel-independent masked autoencoder graph structure domain generalization`
20. `state conditioned dynamic graph trust gate multivariate time series 2025`
21. `2023 2024 source domain environments worst-group threshold calibration anomaly detection conformal`
22. `site:proceedings.mlr.press 2023 2024 group conditional conformal calibration worst group`
23. `site:openreview.net anomaly detection worst group calibration threshold environment`
24. `multi-environment quantile calibration false positive anomaly detection distribution shift paper 2024`
25. `site:arxiv.org "suffix automaton" anomaly detection time series 2023 2024 2025`
26. `site:arxiv.org vector quantization autoregressive prediction time series anomaly detection 2023 2024 2025`
27. `site:dl.acm.org suffix automaton network intrusion detection behavior sequence`
28. `site:arxiv.org discrete behavior code normal prediction residual anomaly detection time series`
29. `"SAM Decoding" suffix automaton paper`
30. `"Suffix Automaton" decoding language model arxiv 2411.10666`
31. `arxiv 2411.10666 github`
32. `site:github.com 2411.10666 suffix automaton`
33. `"vector quantized" "time series anomaly detection"`
34. `"VQ-VAE" "time series anomaly detection" paper`
35. `"discrete codes" "anomaly detection" time series autoregressive`
36. `"behavior sequence" suffix automaton intrusion detection`
37. `"JCCMTM" paper pdf authors`
38. `"JCCMTM" arxiv`
39. `"Curated Test-Time Adaptation for Multivariate Time-Series Anomaly Detection Under Distribution Shift"`
40. `"CANDI" multivariate time-series anomaly detection arxiv`
41. `"JCCMTM" pdf Qi Li Zhenyu Zhang`
42. `"10.1016/j.neunet.2025.107922" pdf`
43. `"107922" "JCCMTM" filetype:pdf`
44. `"Joint channel-independent and channel-dependent strategy" pdf`
45. `site:github.com/Torea-L/JCCMTM`
46. `github Torea-L JCCMTM paper pdf`
47. `RWKV intrusion detection network security arxiv`
48. `RWKV anomaly detection time series arxiv 2024 2025 2026`
49. `RWKV-7 time series anomaly detection`
50. `RWKV network traffic classification paper`
51. `2023 2024 2025 cross-year network intrusion detection temporal drift evaluation paper`
52. `"cross-year" network intrusion detection 2024`
53. `network intrusion detection temporal generalization year-to-year concept drift paper 2025`
54. `LSPR23 LSPR24 intrusion detection cross-year`
55. `"COMET: Codebook-based Online-adaptive Multi-scale Embedding" official code`
56. `site:github.com "COMET: Codebook-based Online-adaptive Multi-scale Embedding"`
57. `site:github.com Jinwoo Park Hyeongwon Kang COMET time-series anomaly`
58. `"DyG-Mamba: Continuous State Space Modeling on Dynamic Graphs" official code OpenReview`
59. `site:github.com/Clearloveyuan/DyG-Mamba`
60. `site:openreview.net/forum?id=ja2wA4UncJ DyG-Mamba`
61. `site:arxiv.org/abs/2511.15083 Fourier-KAN-Mamba`
62. `"JCCMTM" "107922" official code paper`
63. `"JCCMTM: Joint channel-independent and channel-dependent" filetype:pdf`
64. `"JCCMTM" "Neural Networks" 107922 PDF`
65. `"JCCMTM" Qi Li BUPT author manuscript`
66. `"10.1016/j.neunet.2025.107922" "pdf"`
67. `site:openreview.net multivariate time series masked pretraining channel independent channel dependent 2023 2024`
68. `site:arxiv.org time series OOD generalization stable private representation environment inference 2023 2024 2025`
69. `site:arxiv.org TimeVQVAE-AD 2024 anomaly detection vector quantization`
70. `site:arxiv.org frequency-aware Mamba time series anomaly detection 2024 2025`
71. `site:proceedings.mlr.press/v235 "UP2ME: Univariate Pre-training"`
72. `site:github.com/Thinklab-SJTU/UP2ME "UP2ME"`
73. `"masked pretraining" "state-conditioned graph" multivariate time series 2024 2025`
74. `network traffic semantic field group masked pretraining graph RWKV`
75. `site:openreview.net "univariate pre-training" multivariate graph anomaly detection`
76. `site:arxiv.org "channel decoupling" "dependency graph" time series anomaly`

## 当前来源池与状态

| 来源 | 官方入口／原件 | 当前证据等级 | 初步关联 | Zotero | 待办 |
|---|---|---|---|---|---|
| RTTAD | `raw/papers/attack-detection/2026-Huang-RTTAD-Risk-Aware-Test-Time-Adaptation.pdf` | 由 C12 专用代理完成全文核验 | C12 最近邻；本任务不重复扩展引用链 | 见 C12 专项报告 | 只链接专项裁决 |
| NetGuard | `raw/papers/attack-detection/2025-Gupta-NetGuard-Generative-Active-Adaptation-NIDS.pdf` | A 级全文＋作者页 | 跨时间漂移网络入侵检测；与 C 的源域冻结合同不同 | 父 `4N4DE8HP`；附件 `BPABL3B6` | 已完成 |
| JSSM | `raw/papers/attack-detection/2024-Chen-Joint-SSM-Detrending-Anomaly-Detection.pdf` | A 级全文 | B 的状态空间异常检测近邻 | 父 `GDGFI4CY`；附件 `HKYZCHKY` | 已完成 |
| FOIL | `raw/papers/methodology/2024-Liu-FOIL-Time-Series-OOD-Invariant-Learning.pdf` | A 级正式全文＋官方源码 | C 的时间环境／不变学习近邻 | 父 `NJFG5749`；附件 `734K72TF` | 已完成 |
| SAM Decoding | `raw/papers/methodology/2024-Hu-SAM-Decoding-Suffix-Automaton.pdf` | A 级正式全文＋官方源码 | D 的后缀自动机数据结构近邻 | 父 `DYBA9QVH`；附件 `AMY65RNU` | 已完成 |
| JCCMTM | DOI `10.1016/j.neunet.2025.107922`；官方源码 `https://github.com/Torea-L/JCCMTM` | B 级期刊摘要／落地页＋官方源码；全文受限 | A 的通道独立＋通道依赖掩码建模直接近邻 | 父 `HHR2DZQF`；无附件 | 已固定访问阻塞；不伪造全文笔记 |
| UP2ME | `raw/papers/methodology/2024-Zhang-UP2ME-Univariate-Pretraining-Multivariate-Finetuning.pdf`；PMLR `v235/zhang24al` | A 级正式全文＋官方源码 | A 的通道解耦掩码预训练→冻结表示稀疏图→异常检测微调直接近邻 | 父 `DXHAIWLN`；附件 `FGFYF7AQ` | 已完成 |
| Lens | `raw/papers/traffic-foundation-models/2402.03646_Lens_流量T5基础模型.pdf`；arXiv `2402.03646` | 既有 A 级全文笔记 | A 的网络知识引导字段边界掩码先例 | 父 `X9E6ZBPV`；附件 `FTE7VMND` | 已复用并补四栏 |
| FlowSem-MAE | `raw/papers/traffic-foundation-models/2603.10051_FlowSem-MAE_协议原生表格MAE.pdf`；arXiv `2603.10051` | 既有 A 级全文笔记 | A 的协议字段表、字段专属嵌入、可预测性过滤与双轴建模先例 | 父 `HH8TZ7I4`；附件沿既有记录 | 已复用并补四栏 |
| DyG-Mamba | `raw/papers/methodology/2024-Dyg-Mamba-Continuous-Time-Dynamic-Graph.pdf`；arXiv `2408.06966`；OpenReview `ja2wA4UncJ` | A 级全文＋官方源码 | B 的真实时间跨度连续状态和稳定性直接近邻 | 父 `NFRXRHB9`；附件 `AY5854Q7` | 已完成 |
| Fourier-KAN-Mamba | arXiv `2511.15083` | 撤稿／摘要证据，未取得官方全文 | B 的频域＋Mamba＋门控筛选线索 | 未导入 | 核官方撤稿记录后列阻塞，不用缓存副本冒充全文 |
| COMET | `raw/papers/attack-detection/2026-COMET-Codebook-Memory-Time-Series-Anomaly-Detection.pdf`；arXiv `2602.01635` | A 级全文 | D 的向量量化正常模式记忆直接近邻 | 父 `58PMB8WD`；无附件，全文见 raw | 已完成；作者源码未发现 |
| CBSeq | `raw/papers/attack-detection/encrypted/2023-Cui-CBSeq-Encrypted-Malware.pdf` | 既有全文笔记 | D 的去身份行为序列先前工作 | 父 `WI45ZNS8` | 已复用并补四栏 |
| PLM-NIDS | `raw/papers/rwkv/2026_Sharma_PLM-NIDS_RWKV协议语言网络入侵检测.pdf` | 既有全文笔记 | D 的正常序列预测残差／困惑度先前工作 | 父 `D7MUVS2M` | 已复用并补四栏 |
| 预训练多尺度 RWKV-GCN | `raw/papers/rwkv/2026_Hao_Pre-trained_Multi-scale_RWKV-GCN_Multivariate_Forecasting.pdf` | 既有全文笔记 | A 的通道独立掩码预训练→图建模强近邻 | 父 `XSXYQ6EB`；附件 `T5CCRLL4` | 已复用、补四栏并补 Zotero |
| RWKV-7／RWKV-8 官方资料 | 本地既有全文、笔记与官方仓库资源笔记 | 全文＋官方源码 | A—D 的架构来源；不构成网络检测效果证据 | RWKV-7 父 `A4M74UVI` | 已复用并补四栏 |

## 已完成全文核验的边界

- **A**：泛化的“通道独立／通道解耦掩码预训练后引入跨字段依赖”已被 RWKV-GCN、JCCMTM 和 UP2ME 覆盖；Lens 与 FlowSem-MAE 又封闭了“网络语义字段边界掩码／字段专属建模”主张。UP2ME 直接覆盖冻结编码器潜表示构图与异常检测微调，故为高同构风险。剩余边界只能是由源掩码预测一致性监督的 RWKV 因果状态可信边、严格冻结跨年合同及其可证伪联合；“语义组”本身也不能再称原创。
- **B**：连续时间／时间间隔控制状态、选择性状态空间异常检测、频域分支和门控均有先前工作，不能分别写成首创。剩余边界可能是对 RWKV-7 广义 Delta 的连续时间改写、非扩张／有界信任约束、因果滚动频谱与 2-IP 网络表征的特定组合。
- **C**：由时间邻接推断环境并做不变学习已被 FOIL 覆盖；最坏源环境分位阈值也应视为保守校准组合，不宜单独宣称新理论。剩余边界可能是稳定／私有 RWKV 状态分解、严格源域冻结、与最坏源环境告警规则的联合。
- **D**：行为序列、正常序列预测分数、后缀自动机、离散代码本／正常记忆均分别存在。尚未发现“去身份行为码＋ROSA／后缀自动机＋正常预测残差”的完整同构方法；原创性最多落在受限任务组合与冲突消解，不应宣称各模块原创。
- **C12**：RTTAD、TTA-AD、CANDI、DeltaNet 与污染鲁棒适应链由专用代理完成全文核验；本任务只链接专项报告，不重复扩展。

## 下一步

1. C12 专项报告已经落盘，主报告中的链接与数量已经核对。
2. Markdown 结构、路径、数量、Zotero 和空白错误自检已经完成。
3. 本轮不再扩展引用链；后续只由真实快速消融改变候选排序。

## 最终恢复状态

- A—D 联网查重已完成，主报告路径为 `.Codex/docs/RWKV/candidates/2026-08-11-RWKV候选联网同构方法查重.md`。
- 共记录 76 条查询式；纳入 13 篇全文证据与 2 项摘要／无法获取全文证据。
- 新增 7 份 raw PDF、7 篇论文全文笔记、6 篇官方源码／作者页笔记、10 个 Zotero 父条目与 8 个全文附件。
- 风险与实验排序：C＞A＞B＞D；A、B、D 为高同构风险，C 为中高风险；全部结论均为原创边界与实验优先级裁决，不构成有效性证据。
- C12 最近邻链由专项报告独立承担；2026-08-11 终检为 10 篇独立全文／12 份 PDF／10 篇笔记／10 条 Zotero 记录，后续数量以专项闭合台账为准。
- 所有计划内验收均已完成；没有待办的全文、入库或链接工作。

## 全文核验记录

### FOIL（Liu 等，ICML 2024）—已完成

- **查询式**：`site:proceedings.mlr.press 2023 2024 time series out-of-distribution generalization invariant learning environment robustness`；`2023 2024 source domain environments worst-group threshold calibration anomaly detection conformal`。
- **官方来源**：https://proceedings.mlr.press/v235/liu24ae.html；https://github.com/AdityaLab/FOIL。
- **本地原件**：`raw/papers/methodology/2024-Liu-FOIL-Time-Series-OOD-Invariant-Learning.pdf`。
- **证据等级**：A级；ICML/PMLR 正式全文＋官方源码，页级方法、消融和讨论均已核验。
- **关键页码**：第 2 页式（1）最差环境训练风险；第 3 页时间序列无环境标签及未观测变量问题；第 4 页三模块与测试期只用 MTIL；第 5 页式（5）—（10）表示空间环境推断、时间邻接传播与跨环境损失方差；第 6 页等长时间段初始化；第 7 页环境推断／邻接传播消融；第 9 页讨论与未解决项。
- **与候选 C 的判断**：时间环境推断＋跨环境不变表示为**强重叠**；最差环境训练风险与候选 C 的最坏源环境分位告警不是同一机制。FOIL 不覆盖稳定／私有 RWKV 状态分解、网络入侵检测和告警阈值校准。
- **主张修订**：候选 C 不得宣称首次用时间环境或不变学习应对时间序列分布外泛化；可写边界限定为严格源域冻结下的稳定／私有 RWKV 状态与最坏源环境告警规则之联合。
- **制品**：`wiki/papers/methodology/2024-Liu-FOIL时间序列OOD不变学习.md`；`wiki/resources/AdityaLab-FOIL官方源码.md`；两个对应索引均已入链。
- **Zotero**：已导入“我的文库”，父条目键 `NJFG5749`，全文附件键 `734K72TF`；导入前按完整题名与 arXiv:2406.09130 去重均无结果。
- **待办**：在候选 C 汇总后再做一轮引用链扩展；若没有改变原创边界即停止。

### SAM Decoding（Hu 等，ACL 2025）—已完成

- **查询式**：`site:arxiv.org "suffix automaton" anomaly detection time series 2023 2024 2025`；`"SAM Decoding" suffix automaton paper`；`"Suffix Automaton" decoding language model arxiv 2411.10666`；`site:github.com 2411.10666 suffix automaton`。
- **官方来源**：https://aclanthology.org/2025.acl-long.595/；https://github.com/hyx1999/SAM-Decoding。
- **本地原件**：`raw/papers/methodology/2024-Hu-SAM-Decoding-Suffix-Automaton.pdf`。
- **证据等级**：A级；ACL Anthology 正式全文＋官方源码，方法、均摊复杂度证明、消融和限制均已页级核验。
- **关键页码**：第 2 页标准后缀自动机与均摊更新／检索复杂度；第 3 页静态／动态双自动机；第 4 页算法 1、最长后缀位置与匹配长度、均摊 `O(1)`／单步最坏 `O(L)`；第 5 页验证后增量更新和按匹配长度切换支路；第 7—8 页超参数及移除静态／动态自动机消融；第 9 页语料依赖、启发式门控和真实评价限制；第 11—12 页势能法复杂度证明。
- **与候选 D 的判断**：后缀自动机精确重复匹配、静态＋动态记忆、按匹配长度门控为**强重叠**；论文不覆盖固定容量 ROSA、去身份流量行为码、异常检测或正常预测残差。候选 D 的完整组合尚未发现同构，但 M1 不能单独作为原创。
- **主张修订**：不得宣称首次用后缀自动机做神经序列在线重复匹配或按匹配长度选择支路；不得把标准自动机的复杂度直接写成 ROSA 的复杂度。
- **制品**：`wiki/papers/methodology/2025-Hu-SAM-Decoding后缀自动机推测解码.md`；`wiki/resources/hyx1999-SAM-Decoding官方源码.md`；两个索引均已入链。
- **Zotero**：已导入“我的文库”，父条目键 `DYBA9QVH`，全文附件键 `AMY65RNU`；导入前按题名、DOI 与 arXiv:2411.10666 三重去重均无结果。
- **待办**：继续核 COMET／CBSeq／PLM-NIDS 组合近邻，裁定候选 D 是否仍能保留组合原创边界。

### JSSM（Chen 等，IEEE SPL 2024）—已完成

- **查询式**：`site:arxiv.org 2023 2024 2025 frequency-domain state space model time series anomaly detection Mamba Fourier`；`RWKV anomaly detection time series arxiv 2024 2025 2026`；题名精确查询与 DOI 入口核验。
- **官方来源**：https://arxiv.org/abs/2405.19823；https://doi.org/10.1109/LSP.2024.3438078。
- **本地原件**：`raw/papers/attack-detection/2024-Chen-Joint-SSM-Detrending-Anomaly-Detection.pdf`。
- **证据等级**：A级；IEEE 正式论文的作者公开全文、arXiv 官方元数据与 DOI 三者一致，方法和消融已逐页核验。官方源码题名搜索遇到 GitHub 公开搜索 429，正文无源码链接，因此源码状态为“未发现”，不是“不存在”。
- **关键页码**：第 1 页任务与贡献；第 2 页式（1）—（3）S6 更新和 HP 去趋势；第 3 页式（4）—（10）DMamba、傅里叶峰值选移动平均窗口、重建分数；第 3—4 页数据／基线／评价；第 4 页表 3 去趋势模块消融与结论。
- **与候选 B 的判断**：选择性状态空间异常检测为**强重叠**，频谱辅助非平稳分解为**中等重叠**；JSSM 的网络生成 `Δ` 不是物理时间间隔，傅里叶只选移动平均核宽，也没有 RWKV-7 广义 Delta、因果谱支路或有界信任残差。
- **主张修订**：候选 B 不得宣称首次用选择性状态空间模型做异常检测，或首次把频谱信息与 SSM-TSAD 结合；可写边界需精确限定为真实 `Δt` 驱动的 RWKV-7 广义 Delta 连续化及非扩张／有界因果融合。
- **制品**：`wiki/papers/attack-detection/2024-Chen-JSSM去趋势状态空间异常检测.md`；攻击检测索引已入链。
- **Zotero**：已导入“我的文库”，父条目键 `GDGFI4CY`，全文附件键 `HKYZCHKY`；导入前按题名、DOI 和 arXiv 三重去重均无结果。
- **待办**：DyG-Mamba 核真实时间间隔连续状态，Fourier-KAN-Mamba 核独立频域支路与门控；两者决定 B 的最终风险。

### NetGuard（Gupta 等，arXiv 2025）—已完成

- **查询式**：`site:arxiv.org 2023 2024 2025 network intrusion detection concept drift cross-year temporal distribution shift`；`2023 2024 2025 cross-year network intrusion detection temporal drift evaluation paper`；`network intrusion detection temporal generalization year-to-year concept drift paper 2025`；完整题名＋GitHub；作者 Shinan Liu 公开履历。
- **官方来源**：https://arxiv.org/abs/2503.03022；https://www.shinan.info/wp-content/uploads/2026/03/cv.pdf。
- **本地原件**：`raw/papers/attack-detection/2025-Gupta-NetGuard-Generative-Active-Adaptation-NIDS.pdf`。
- **证据等级**：A级方法证据；arXiv v3 全文、官方元数据与作者页一致。发表状态只到预印本／在投，不能把 PDF 模板视为 KDD 接收。题名 GitHub 查询未发现作者源码。
- **关键页码**：第 1 页跨年／跨月 NIDS 漂移动机；第 4 页闭环主动适应；第 4—5 页双 GMM 选样、预言机真值标注和训练集更新；第 5—6 页条件生成、身份／端口／时间戳特征与合成过滤；第 6 页目标样本排除、0.1%–1% 标签预算、双向 CIC 与 UGR 月份设置、对抗漂移范围外；第 7—8 页端到端结果与生成消融；第 11 页敏感性和成本。
- **与 A—D 的判断**：四候选均为低机制重叠。NetGuard 是候选 C 的高任务近邻，但它读取目标分布、取得目标真值标签并重训，严格违反候选 C 的源域冻结信息预算；对 A／B 无结构重叠；与 D 的去身份合同相反。
- **主张修订**：A—D 均不得宣称首次处理跨时间 NIDS 漂移；应把 NetGuard 列为带目标标签的适应参考上界，不得当作共同信息预算主基线。
- **制品**：`wiki/papers/attack-detection/2025-Gupta-NetGuard漂移与不均衡NIDS主动适应.md`；`wiki/resources/Shinan-Liu作者履历.md`；两个索引均已入链。
- **Zotero**：已导入“我的文库”，父条目键 `4N4DE8HP`，全文附件键 `BPABL3B6`；导入前按题名和 arXiv 双重去重均无结果。
- **待办**：引用链只保留与 A—D 机制直接相关者；带目标标签主动适应不再扩展，避免偏离源域冻结问题。

### COMET（Park 等，arXiv 2026）—已完成

- **查询式**：`"COMET: Codebook-based Online-adaptive Multi-scale Embedding" official code`；`site:github.com "COMET: Codebook-based Online-adaptive Multi-scale Embedding"`；`site:github.com Jinwoo Park Hyeongwon Kang COMET time-series anomaly`。
- **官方来源**：https://arxiv.org/abs/2602.01635；完整题名 GitHub 查询及 GitHub 仓库接口检索结果为 0，故只记“未发现作者源码”。
- **本地原件**：`raw/papers/attack-detection/2026-COMET-Codebook-Memory-Time-Series-Anomaly-Detection.pdf`。
- **证据等级**：A级全文证据；arXiv v2 原论文逐页核验。发表身份只写预印本，不推断会议接收。
- **关键页码**：第 3 页式（5）—（7）多尺度融合与最近代码量化；第 4 页式（8）—（12）VQ 训练和训练激活核心集；第 4—5 页式（13）—（20）局部尺度记忆距离、量化误差与双分数；第 6 页式（21）—（25）激活索引伪标签、仅伪正常重建和代码本更新；第 7—8 页表 2 完整组件消融；第 13—14 页算法确认“当前批次先计分、再更新”。
- **与候选 D 的判断**：有限离散正常原型、记忆距离、量化残差和在线正常记忆更新为**强重叠**；COMET 不含去身份行为码、后缀自动机或正常下一码似然。完整候选 D 组合尚未发现同构，但其“代码本正常记忆”不得作为原创。
- **四栏结论**：可借鉴源正常激活索引、局部尺度距离和双分数；不能再主张离散正常代码本／原型距离原创；可实质改造成“RWKV 下一行为码残差＋冻结源正常状态原型距离”；最小消融比较下一码、静态 VQ、二者联合和局部尺度，并以 COMET、PLM-NIDS、CBSeq、SAM Decoding 为强近邻。
- **制品**：`wiki/papers/attack-detection/2026-Park-COMET代码本在线适应异常检测.md`；攻击检测索引已入链。
- **Zotero**：父条目 `58PMB8WD`；导入前按题名和 arXiv 双重去重无结果。Connector 未自动建立附件，本轮以明确的“无附件”状态结案；本地 raw 全文证据完整可用。
- **待办**：总报告中把 COMET 完整测试时适应版单列额外目标信息预算；不扩展其 C12 引用链。

### DyG-Mamba（Li 等，NeurIPS 2025）—已完成

- **查询式**：`"DyG-Mamba: Continuous State Space Modeling on Dynamic Graphs" official code OpenReview`；`site:github.com/Clearloveyuan/DyG-Mamba`；`site:openreview.net/forum?id=ja2wA4UncJ DyG-Mamba`。
- **官方来源**：https://arxiv.org/abs/2408.06966；https://openreview.net/forum?id=ja2wA4UncJ；https://github.com/Clearloveyuan/DyG-Mamba。
- **本地原件**：`raw/papers/methodology/2024-Dyg-Mamba-Continuous-Time-Dynamic-Graph.pdf`；arXiv v2 页面标记 2025-12-18 修订和 NeurIPS 2025 接收。
- **证据等级**：A级；正式会议身份、原论文全文与官方源码三者一致。OpenReview 直接 PDF 请求返回 403，但 arXiv v2 是完整作者公开全文，不构成全文缺失。
- **关键页码**：第 4 页式（7）—（10）连续 SSM；第 5 页式（11）真实跨度的单调有界映射及定理 4.1 负实部状态特征值；第 6 页式（12）—（14）输入依赖 `B,C`、谱范数约束和扰动界；第 8 页表 5—6 的时间信息／跨度函数消融；第 9—10 页加噪边与结论；第 14 页只处理边新增、小数据和跨域未知等限制。
- **与候选 B 的判断**：真实不规则时间间隔控制状态、单调增强遗忘、非扩张状态和输入投影稳定性为**强重叠**；论文不含 RWKV-7 广义 Delta、异常检测或因果频谱残差。候选 B 不能再主张“物理间隔连续状态”本身原创。
- **四栏结论**：可借鉴式（11）、负实部特征值和谱范数约束；不能再主张首次按物理间隔控制 Mamba/SSM；可把物理跨度限定为 RWKV-7 旧状态保留上界、内容只控制定向移除／写入；最小消融比较无间隔、内容 Delta、线性／裁剪间隔、单调有界间隔和频谱残差，强基线含 DyG-Mamba 控制律移植版、JSSM、普通 RWKV-7。
- **官方源码**：只读 `HEAD=ce54319e97560593c8ee704c8df65f5c6f95fd8c`；`models/DyGMamba.py` 含跨度构造，`models/mamba_simple.py` 含 `MambaTimeDelta`；根目录无许可证，当前提交未检索到 `spectral_norm` 同名实现。
- **制品**：`wiki/papers/methodology/2025-Li-DyG-Mamba连续状态空间动态图.md`；`wiki/resources/Clearloveyuan-DyG-Mamba官方源码.md`；两处索引均已入链。
- **Zotero**：父条目 `NFRXRHB9`，全文附件 `AY5854Q7`；导入前按题名与 arXiv 双重去重均无结果。
- **待办**：总报告将论文公式证据与当前源码复现风险分开，不据此推断候选 B 的 LSPR 效果。

### UP2ME（Zhang 等，ICML 2024）—已完成

- **查询式**：`site:openreview.net multivariate time series masked pretraining channel independent channel dependent 2023 2024`；`site:proceedings.mlr.press/v235 "UP2ME: Univariate Pre-training"`；`site:github.com/Thinklab-SJTU/UP2ME "UP2ME"`。
- **官方来源**：https://proceedings.mlr.press/v235/zhang24al.html；https://github.com/Thinklab-SJTU/UP2ME。
- **本地原件**：`raw/papers/methodology/2024-Zhang-UP2ME-Univariate-Pretraining-Multivariate-Finetuning.pdf`。
- **证据等级**：A级；ICML／PMLR 正式全文、官方代码与论文方法相互一致，方法、异常检测任务、消融和限制均已页级核验。
- **关键页码**：第 1—2 页总体流程与贡献；第 3 页式（1）—（5）可变窗口、通道解耦和掩码自动编码；第 4 页式（8）逐补丁重建异常分数及“同数据集、非严格零样本”脚注；第 4—5 页式（9）冻结编码器潜表示余弦稀疏图和式（10）时间—通道层；第 5 页逐数据集预训练合同；第 6 页预训练与构图消融；第 9 页分类和跨数据集限制。
- **与候选 A 的判断**：通道解耦掩码预训练、冻结预训练编码器、由潜表示构造稀疏跨通道图、图微调和异常检测下游形成**整链强重叠**。论文不覆盖网络字段语义分组、RWKV 因果状态可信边或 LSPR23→LSPR24 严格冻结。
- **主张修订**：候选 A 不得宣称首次提出“逐字段／通道解耦预训练后恢复跨字段依赖”、首次用冻结预训练表示构图，或首次将该范式用于异常检测；只可把原创边界限定为源网络语义组掩码目标直接监督 RWKV 因果状态可信边，并冻结迁移到目标年度。
- **四栏结论**：可借鉴式（1）—（5）、式（8）—（10）；不能再主张通用逐变量预训练→潜表示图链条原创；可让 LSPR23 语义组掩码预测一致性成为边可信监督，而非另叠通用图模块；最小消融比较普通逐字段掩码、UP2ME 式余弦图、固定语义图、状态可信图与无预训练，强基线含 UP2ME、JCCMTM、预训练多尺度 RWKV-GCN、普通 RWKV。
- **官方源码**：`HEAD=6fd70378870a0bab8627c39def660e483c4dc1d9`，Apache-2.0；`UP2ME_detector.py` 冻结预训练模型并构图，`graph_structure.py` 实现近邻图与全局前 `kC` 边的交集。
- **制品**：`wiki/papers/methodology/2024-Zhang-UP2ME逐变量预训练与多变量图微调.md`；`wiki/resources/Thinklab-SJTU-UP2ME官方源码.md`；两处索引均已入链。
- **Zotero**：父条目 `DXHAIWLN`，全文附件 `FGFYF7AQ`；导入前按完整题名、OpenReview 标识和 PMLR URL 三重去重均无结果。
- **待办**：执行一轮 UP2ME 后边界确认查询；若未发现更近的源语义／状态可信图方法，停止扩展并在总报告将 A 标为高风险。

## 摘要／元数据证据与无法获取全文

### JCCMTM（Li 等，Neural Networks 2025）—全文受限

- **查询式**：`"JCCMTM" paper pdf authors`；`"10.1016/j.neunet.2025.107922" pdf`；`"JCCMTM: Joint channel-independent and channel-dependent" filetype:pdf`；`"JCCMTM" Qi Li BUPT author manuscript`；官方仓库文件树核验。
- **官方来源**：https://www.sciencedirect.com/science/article/pii/S0893608025008032；https://pubmed.ncbi.nlm.nih.gov/40779936/；https://github.com/Torea-L/JCCMTM。
- **本地原件**：无。ScienceDirect 明示机构访问／购买 PDF；ResearchGate 只提供请求全文；作者仓库不含 PDF 或作者稿。
- **证据等级**：B 级；正式期刊摘要、期刊导言公开片段、PubMed 元数据和官方源码。不得升级为全文证据。
- **关键页码**：无；未取得全文，禁止伪造页码。官方公开摘要只确认联合 CI/CD 掩码预训练、TSaS、Uni-Mul 变换、稀疏注意力／全局词元降复杂度以及预测／异常检测下游任务。
- **与候选 A 的判断**：联合通道独立／通道依赖掩码时间序列预训练为**直接组件重叠**；官方源码公开 `CI`、`CD`、`CICD` 以及逐通道 `Uni`、跨通道 `Multi` 和 `Uni-to-Mul` 路径。候选 A 不得宣称该抽象组合首创，但源语义组约束、状态条件可信边和 RWKV 跨年冻结仍未被该摘要／源码覆盖。
- **四栏结论**：可借鉴双流 CI/CD 和从逐通道到跨通道的显式变换；不能再主张联合 CI/CD 掩码预训练原创；可实质改造成“源语义组掩码 RWKV 状态预训练＋由源时间一致性约束的状态条件边”，而不是通用双流注意力；最小消融比较 CI、CD、CICD、固定语义图和状态条件可信图，强基线含 JCCMTM 与预训练多尺度 RWKV-GCN。
- **官方源码**：`HEAD=ccf61cdbbacb417130f4d43353893889ff240656`，Apache-2.0；制品 `wiki/resources/Torea-L-JCCMTM官方源码.md` 已入资源索引。
- **Zotero**：父条目 `HHR2DZQF`；导入前按题名和 DOI 双重去重无结果；无 PDF 附件。
- **待办**：若用户未来合法取得全文，建议原件名 `raw/papers/methodology/2025-Li-JCCMTM-Masked-Multivariate-Time-Series.pdf`，再补公式、消融和限制页码；当前任务不继续绕过付费访问。

### Fourier-KAN-Mamba（Wang 等，arXiv 2025／2026 撤稿）—官方全文不可用

- **查询式**：`site:arxiv.org 2023 2024 2025 frequency-domain state space model time series anomaly detection Mamba Fourier`；`site:arxiv.org/abs/2511.15083 Fourier-KAN-Mamba`；arXiv PDF 入口核验。
- **官方来源**：https://arxiv.org/abs/2511.15083。
- **本地原件**：无。arXiv v2 官方页显示“No PDF available”与“Withdrawn”，PDF 请求返回 404。
- **证据等级**：C 级官方元数据／摘要；不得支撑公式、实验、消融或可靠机制结论。
- **关键页码**：无。官方摘要只披露 Fourier 层、KAN、Mamba 和时间门组合；官方撤稿说明指出异常分数识别机制的理论分析有缺陷，且主要依据指标观察、缺少充分视觉或实证验证，可能影响相关结论可靠性。
- **与候选 B 的判断**：只能证明“频域＋KAN＋Mamba＋时间门”这一宽泛组合曾被公开披露，不能证明与候选 B 的因果滚动频谱、真实 `Δt`、RWKV-7 广义 Delta 或有界信任残差同构。
- **四栏结论**：摘要层面不建议直接借鉴公式；不能宣称广义的“首次结合频域与 Mamba 做异常检测”；可研究严格因果且有幅度界的频谱残差与 RWKV-7 连续状态，但必须由 JSSM／DyG-Mamba 的可靠全文和本课题实验支撑；最小消融比较普通去趋势、JSSM 式傅里叶选窗、因果谱残差和无频谱版本。
- **Zotero**：未导入；来源已撤稿且无官方全文，不作为可复用正式文献入库。
- **待办**：停止寻找第三方缓存全文，避免把已撤稿版本冒充可靠原件。
