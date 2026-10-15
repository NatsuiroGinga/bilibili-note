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
