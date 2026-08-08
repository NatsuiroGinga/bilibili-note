# RWKV 方案文献证据独立复审笔记

## 范围检查点

### 检索问题表

| 编号 | 核心问题 | 检索概念与同义词 | 判定输出 |
| --- | --- | --- | --- |
| Q1 | RWKV 的递归状态与复杂度事实是什么？ | `RWKV`、`RWKV-7`、`Goose`、`RWKV-8`、`matrix-valued state`、`dynamic recurrence`、`state evolution` | 架构允许主张与版本边界 |
| Q2 | RWKV 是否已有长时序、时间序列、异常检测或网络入侵直接应用？ | `RWKV time series`、`anomaly detection`、`network intrusion detection`、`traffic classification`、`protocol language model` | 与当前创新点一的重合矩阵 |
| Q3 | 非 RWKV 的状态空间流量方法已覆盖哪些输入、任务与实验？ | `Mamba network traffic`、`encrypted traffic classification`、`byte-level traffic`、`long sequence intrusion detection` | 架构新意与任务新意分离 |
| Q4 | 课程学习能否为长尾、时间漂移或历史长度训练提供理论与算法依据？ | `curriculum learning`、`self-paced learning`、`difficulty-aware`、`network intrusion detection`、`long-tail`、`concept drift` | 创新点二课程部分的证据边界 |
| Q5 | 约束强化学习是否适用于本任务，还是对静态分类属于概念误用？ | `constrained reinforcement learning`、`safe RL`、`CMDP`、`classification`、`alarm escalation`、`sequential decision` | 静态检测与序列决策的适用门槛 |
| Q6 | UGR'16 的聚合标签能支持何种题名？ | `UGR'16`、`UGR16`、`netflow`、`one-minute aggregation`、`botnet`、`anomaly`、`ground truth` | “恶意流量检测”与“网络异常状态检测”的允许／禁止措辞 |
| Q7 | 课程与强化学习能否形成一体化训练创新？ | `self-paced reinforcement learning`、`curriculum reinforcement learning`、`teacher-student curriculum`、`context distribution` | 课程分布、策略学习与难度调度的理论接口 |
| Q8 | 固定离线流量序列应使用哪类决策模型？ | `offline constrained reinforcement learning`、`CMDP`、`contextual bandit`、`optimal stopping`、`early time-series classification` | 算法适用条件、不可识别项与推荐顺序 |
| Q9 | RWKV 是否已有序列决策工作？ | `Decision-RWKV`、`MARWKV`、`multi-agent reinforcement learning`、`RWKV policy` | 与“RWKV 状态＋继续／告警／拒识”设定的直接重合 |

### 纳入、排除与证据等级

- 纳入：身份由 DOI、arXiv、ACL、出版社或官方项目页闭合；全文可读；直接涉及 RWKV 结构、时序／异常、网络流量／入侵、课程学习、约束强化学习，或对状态约束有清晰迁移路径。
- 排除：仅二手博客或目录题录；身份无法核验；只有摘要却用于声称公式、消融或数值；模态或任务无可解释迁移路径；重复版本只保留信息最完整版本。
- 一级全文：已取得论文全文并回到 PDF 页码、章节、公式、表格或图核验具体主张。
- 一级页面／元数据：官方论文页、数据页或代码页只支持身份、版本、许可证与公开状态，不支持正文方法细节。
- 二手线索：仅用于发现候选，不进入最终技术结论。

### 主张台账门禁

- 每条核心证据必须写明“来源身份—证据位置—允许主张—禁止主张”。
- “未检索到”只能写成当前证据缺口，不能写成“从未有人研究”。
- 方案设计、预算和预注册门槛仍是待验证假设，不能写成已有结果。
- RWKV-8 若没有可核验正式论文、代码版本与稳定权重，只能登记为待核验版本，不得作为方法基座或新颖性依据。
- 静态分类若没有动作影响后续观测、没有行为策略、奖励／成本和轨迹支持，则不得包装为强化学习。

### 停止条件

- 六阶段全部完成且核心全文达到 8 篇，即可裁决；不为凑数扩大到无关模态。
- 若关键全文缺失导致无法判断创新点重合，列出题名、标识符、官方页面和缺失原因后停止扩大主张。

## 候选文献台账

### RWKV.CN 动态生态目录枚举

- 访问方式：通过 Chrome 浏览器控制打开 `https://www.rwkv.cn/eco/papers`，等待客户端渲染后按可见分页逐页读取；不是静态 HTML 标题或搜索摘要。
- 页面状态：目录显示 235 篇，更新时间为 2026-07-07；实际分页共 20 页，前 19 页各 12 项、末页 7 项，枚举总数 235，按题名去重后仍为 235。
- “序列／强化”分类实际显示 48 篇、4 页，每页 12 项；已全部枚举。
- 与本任务直接相关的目录命中：
  - `Optimizing Robotic Manipulation with Decision-RWKV: A Recurrent Sequence Modeling Approach for Lifelong Learning`，目录分类“序列／强化”，外部入口闭合到 arXiv:2407.16306。
  - `Modern Sequence Models in Context of Multi-Agent Reinforcement Learning`，目录分类“序列／强化”，外部入口闭合到奥地利约翰内斯·开普勒大学学位论文库 `titleinfo/10580112`；是否存在正式论文版仍待全文核验。
  - `Training Language Models for Social Deduction with Multi-Agent Reinforcement Learning`，目录分类“序列／强化”，外部入口闭合到 arXiv:2502.06060。
  - `PLM-NIDS`，目录分类“序列／强化”，已由本地全文独立核验。
  - `AutoGMM-RWKV`，目录分类“序列／强化”，外部入口闭合到 IEEE 文献号 10729884。
  - 异常检测相关目录命中包括 `Spatio-Temporal Weighted Graph Reason Learning for Multivariate Time-Series Anomaly Detection`、`A Method for Detecting Spatio-temporal Correlation Anomalies of WSN Nodes...`、`Injecting Explainability and Lightweight Design into Weakly Supervised Video Anomaly Detection Systems`；它们必须回到一级全文后才可判断是否纳入。
- 未发现题名或目录摘要直接对应“早期网络流量分类／最优停止”的 RWKV 论文；`ASSCG` 的“查询／缓存／丢弃”是相邻序列门控线索，但任务域为自动驾驶，不能代替早期告警理论。
- 证据边界：RWKV.CN 仅作为候选发现入口；其中文摘要、分类和“最佳”等措辞均不进入核心结论。

### 指定候选：arXiv:2607.02292

- 身份：Juan Agustín Duque、Sergio García-Heredia、Vinicius Hernandes、Eliška Greplová、Thomas Spriggs、Aaron Courville、Anna Dawid，`One More Time: Revisiting Neural Quantum States from a Reinforcement Learning Perspective`，arXiv:2607.02292v1，2026-07-02 提交，34 页。
- 目录位置：RWKV.CN “全部”第 1 页第 1 项；“序列／强化”筛选第 1 页第 1 项。
- 全文状态：已读取 arXiv 实验性 HTML 全文，重点核验正文第 2.1、3、5.5 节和附录 C.3、C.4、D.8；尚未下载 PDF 或建立 wiki 笔记，因为当前判定为边界旁证而非方案可直接采用的核心论文。
- 实际方法：论文把特定条件下的神经量子态变分能量最小化写成优势策略梯度形式，提出概率比与相位增量双裁剪的近端波函数优化；RWKV 仅作为 1.5B 参数 RWKV-7 自回归神经量子态，在 `N=12` 的一维横场 Ising 模型上微调。
- 允许主张：RWKV-7 能作为大规模自回归神经量子态，并能用近端目标在非标准物理优化任务上微调；作者给出局部的一阶一致性与裁剪改进界。
- 禁止主张：该论文不能证明静态流量分类适合 PPO／CPO，不能证明课程学习、多尺度网络状态或恶意流量检测有效，也不能把局部改进界扩张为神经网络全局收敛；全文附录 C.4 明确承认共同支撑、有界性及局部理论限制。
- 纳入角色：**边界旁证**，只用于说明“RWKV-7＋近端式非标准目标”在别的生成分布任务中可实现；不计入恶意流量或早期告警的直接核心证据。

## 全文证据台账

- 核心全文 14 篇：RWKV 原始论文、Eagle/Finch、RWKV-7、RWKV-TS、PLM-NIDS、NetMamba、Decision-RWKV、课程学习、自步深度强化学习、CPO、COPO、FIRMBOUND、UGR’16 原始论文、UGR’16 数据质量论文。
- 边界全文：RWKV-X、MambaNetBurst、AgentDojo、`arXiv:2607.02292`。
- 新增原件 8 份，均已计算 SHA-256、验证页数并链接到结构化论文笔记。
- AutoGMM-RWKV 与 MARWKV 因出版社或机构仓储访问阻断，仅列入手动下载清单，未用于核心论断。

- 待补。

## 现有方案引用核验

- 待补。

## 综合判断与研究空白

- 裁决：修改后保留。
- 第三章建议冻结为“快慢递归状态＋生成式下一窗口预测”；第四章建议冻结为“自步课程＋外生轨迹监督最优停止”。
- 固定流量分类上的 CPO、COPO、GRPO 主线否决；只有真实动作、转移、奖励与行为覆盖后才能条件采用。
- UGR’16 分钟聚合允许“攻击承载网络状态”与事件级延迟，不允许逐流恶意定位；v3 是 2016 流量的 2025 特征重提取。

- 待补。

## 缺失全文与阻塞

- 并行子代理名额已满，UGR'16 标签语义审计由本代理执行；不影响任务完成。
- AutoGMM-RWKV：IEEE 全文访问受阻；需完整结构、模拟、拆分、消融和限制。
- MARWKV：JKU 仓储对自动访问返回 403；需作者身份、出版类型、算法、基准和限制。
