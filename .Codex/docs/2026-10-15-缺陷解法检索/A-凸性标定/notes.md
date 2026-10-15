# 检索笔记（持续更新）

## 时间线

### 2026-10-15 T0 启动

- 已完成：建目录；写 `task_plan.md` 与本文件。
- 下一步：本地查重（Zotero 语义检索 + 本地混合索引）→ Scholar 检索（挂代理）→ 核原文。
- 未关闭疑点：
  - PPO adaptive KL 的原文页码/更新式待核（线索称「按实测 KL 与目标 KL 比值在线调整」，须确认是比例式还是分段乘除式）。
  - 是否存在「自适应重放倍数/UTD ratio」的直接文献（未验证）。
- 无法获取原文清单：暂无。

### 2026-10-15 T1 本地查重与既有资产盘点

- **本地库查重结论**：Zotero 语义检索「PPO adaptive KL」「truncated importance sampling」均无命中（相似度全为负），不存在重复入库问题。
- **既有资产 1（强相关）**：Zotero 已有 Gibbs & Candès 2021《Adaptive Conformal Inference Under Distribution Shift》（条目 QED345EG，preprint）——在线闭环更新标定量以应对分布漂移，与本缺陷同构，待核原文更新式。
- **既有资产 2（领域内先例）**：`raw/papers/attack-detection/lamda-related/2023-Kong-在线持续学习的信任域自适应频率.pdf` + 全文笔记已入库。已核：TRAF 的 Eq.(3) `inv'_k = inv'_{k-1} ∓ δ`（按置信分数阈值 ε_fre 步进）、Eq.(4) 上下限截断；调的是 intra-process 触发频率而非复用倍数，无凸映射分析。证据等级：本地全文。
- **既有资产 3**：`raw/.../2019-Cotter-Proxy-Lagrangian-Non-Differentiable-Constraints-JMLR.pdf` 在库，无 wiki 笔记——对偶方法一族的约束处理，待判读。
- 下一条查询：Scholar 验证 PPO adaptive KL 原文 + 检索「adaptive replay ratio / UTD」是否存在。
- 未关闭疑点：PPO 更新式细节（比例式还是分段乘除式）、adaptive UTD 文献存在性。
- 无法获取原文清单：暂无。

### 2026-10-15 T2 Scholar 第一轮完成

**已执行检索式**（均挂代理 127.0.0.1:7890）：
1. `proximal policy optimization`（短查询测试，14 内部查询）
2. `adaptive KL penalty reinforcement learning`
3. `adaptive replay ratio reinforcement learning`
4. `constrained policy optimization dual gradient descent Lagrangian`
5. `PID Lagrangian methods constrained reinforcement learning`
6. `truncated importance sampling off-policy evaluation`
7. `adaptive clipping proximal policy optimization`

**命中与裁定**：
- **C1 PPO**：Schulman et al. 2017, arXiv preprint（46878 引）——确认存在，最高引；原文更新式待下载核验。
- **C2 对偶方法**：Paternain et al. 2019《Constrained RL has zero duality gap》（362 引，NeurIPS）；Ding et al. 2023 last-iterate primal-dual（60 引）——对偶更新作「闭环控制」的理论支柱。
- **C3 PID Lagrangian**：Stooke, Achiam, Abbeel 2020（PMLR，692 引）——确认存在；另有 Peng et al. 2021/2022 Separated Proportional-Integral Lagrangian（28/46 引）。
- **C4 TIS**：经典线（Precup 2000 / Munos 2016 / IMPALA V-trace）未直接命中，需按标题在 arXiv 定位；命中 Metelli et al. 2021《Subgaussian and differentiable importance sampling》（NeurIPS，70 引）——有界 IS 权重，备用。
- **C8 自适应截断（新线索）**：BAPO（ICLR 2026，42 引）balanced policy optimization with adaptive clipping；Zhang et al. 2023《A dynamical clipping approach with task feedback for PPO》；Sha et al. 2026 Dynamic PPO——「把固定截断换成闭环调整」是活跃方向，待核原文是否处理凸性放大。
- **C7 adaptive replay ratio**：**无直接命中**——RL 侧没有找到「自适应重放倍数/UTD」的直接文献；只有 replay buffer 管理/优先级类。这条如实记录为「未找到」。

**下一步**：下载 PPO / RCPO / PID-Lagrangian / V-trace / ACI 五篇 PDF 核原文；查 Zhang 2023 dynamical clipping 的 arXiv ID。
**未关闭疑点**：C4 经典三篇的 arXiv ID；C8 原文细节。
**无法获取原文清单**：暂无。

### 2026-10-15 T3 原文核验完成（六篇全部本地全文）

- **ID 核验**（arXiv API 按标题检索，非搜索引擎）：PPO=1707.06347v2；RCPO=1805.11074v3；PID Lagrangian=2007.03964v1；V-trace/IMPALA=1802.01561；ACI=2106.00170v3；Pb-PPO(dynclip)=2312.07624v3。
- **PDF 已入库 raw/**：`raw/papers/attack-detection/lamda-related/` 六个新 PDF（2017-Schulman、2019-Tessler、2020-Stooke、2018-Espeholt、2021-Gibbs、2023-Zhang）。
- **MinerU 全文已生成 wiki/**：六个 `-全文.md`。
- **公式核验记录**：
  - PPO §4 式 (8) 后：`d<d_targ/1.5 → β←β/2；d>d_targ×1.5 → β←β×2`；原文自述 1.5 与 2 为启发式、算法不敏感。
  - RCPO §3 Eq.(4)(5)：拉格朗日 + 对偶上升 `λ_{k+1}=Γ_λ[λ_k−η₁∇_λL]`，投影到 [0, λ_max]。
  - PID-Lagrangian §4.2 Eq.(13) `λ̇=αg+βġ`；§4.3 Eq.(16) `λ̇=αg+γg̈`；§5 CMDP=动力系统+PID；相关工作段确认 An et al. 2018「SGD=P 控制、动量=PI 控制」先例。
  - V-trace §4.1 Eq.(1)：`ρ_t=min(ρ̄,π/μ)`、`c_i=min(c̄,π/μ)`；c̄=方差缩减、ρ̄=决定收敛不动点（§4.1 末段）。
  - ACI §2 Eq.(2) `α_{t+1}=α_t+γ(α−err_t)`；Eq.(3) 指数加权变体；§A 等价于 pinball loss 的在线梯度下降。
  - Pb-PPO：双层优化 + UCB bandit 在候选截断界集合 ζ 中按 Return 反馈选 ε*。
- **CVaR/DRO 线**：Scholar 确认 Esfahani & Kuhn 2018（3054 引）与 Kisiala 2015 综述（arXiv:1511.00140）；Rockafellar-Uryasev 2000 原文未取（Journal of Risk，无公开 PDF），降为题录级引用。
- **下一条查询**：无需再检索；进入报告撰写。
- **未关闭疑点**：CBF（控制屏障函数）线未深查——如实记录为「未检索」而非「不存在」。
- **无法获取原文清单**：Rockafellar & Uryasev 2000《Optimization of Conditional Value-at-Risk》(Journal of Risk 2(4))——未取得 PDF，仅题录级。

### 2026-10-15 T4 任务完成

- **报告已交付**：`缺陷A-凸性标定-文献解法检索报告.md`（缺陷刻画→候选总表→逐条移植式→E1–E6 最小验证实验→四问回答→未取得原文清单→裁决「需要自创（仅凸性修正一个组件自创）」）。
- **入库完成**（raw/ 6 PDF + wiki/ 6 机械全文 + wiki/ 6 结构化笔记 + INDEX 七处追加）：
  - 2017-Schulman-PPO-自适应KL惩罚系数
  - 2018-Espeholt-IMPALA-V-trace重要性权重截断
  - 2019-Tessler-奖励约束策略优化-对偶梯度下降
  - 2020-Stooke-PID拉格朗日方法-约束RL安全
  - 2021-Gibbs-自适应保形推断-分布漂移在线标定
  - 2023-Zhang-PPO任务反馈动态截断
- **裁决一句话**：闭环控制替代一次性标定有现成多源文献（PPO/RCPO/ACI 可直接落式）；「凸映射放大分布漂移」无对症文献，解析修正与线性化映射需自创；总体**需要自创（组合），但自创面只有一个组件**。
- **过程事故记录（如实）**：报告与两篇笔记的首次生成出现内容损坏（重复短语、乱码占位 token、一次错误路径写入）；已逐处修复并全文重写受影响文件，最终版已通读核对（报告 161 行、六篇笔记各 37–39 行）。错误路径写入的目录已删除。
- **遗留**：CBF 线未检索（如实记录为未查，非不存在）；Rockafellar & Uryasev 2000 仅题录级；未做任何 git 提交（遵守任务约束）。
