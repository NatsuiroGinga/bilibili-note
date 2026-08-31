# 工作笔记：CVaR-pAUC 预算失配数学分析（2026-08-31）

任务：纯数学与源码分析，裁决三种候选修法。不改代码、不跑实验、不连服务器。
本笔记登记证据路径、核验命令与逐项核验状态；结论见同目录 `分析报告.md`。

## 证据清单与核验状态

### 源码（全部本地读取，工作树 `.worktrees/ch4-dtep-pbc-20260819`）

| 文件 | 关键位置 | 已确认内容 |
| --- | --- | --- |
| `thesis/experiments/llm_probe/tools/ch3_ft_entity_ranking_loss.py` | 126–184 | `cvar_pauc_loss`：`k` 只作浮点除数（第 168 行 `/ float(k)`），无 topk、无取整；第 165 行 require 为 `0 < k <= n_neg`（放行 k<1），与第 138 行 docstring「1<=K<=Nn」矛盾 |
| 同上 | 158, 167 | `L_pn = softplus(S_n − S_p)`；relu 在 0 点子梯度取 0（活动判定为严格 `>`） |
| 同上 | 187–203 | `effective_budget`：K_eff = K·n_neg/N_pop，浮点返回不取整；docstring 的无偏性推导（固定 ξ 下）数学正确 |
| 同上 | 206–261 | `CvarThresholdState`：init_value=0.0，惰性建行，commit 显式写回 |
| 同上 | 482–488 | `_quantile_init_xi`：topk 取第 K 大值，仅诊断 `main()`（第 610 行）使用，训练路径不用；docstring 自述「仅用于本诊断脚本」 |
| 同上 | 301–350 | 分层版按 **log2 链长** 分桶（279–287），与分数尾部无关 |
| `tools/ch3_ft_c00_dual_selection.py` | 1629–1631 | 宿主把浮点 K_eff 直接传入损失 |
| 同上 | 1632–1650 | ξ 更新 = 裸 SGD：`xi − 1e-4 * xi.grad`，一次 backward 一步；第 1648 行 `require(xi.grad is not None)` |
| 同上 | 1651–1667 | 诊断只落 `loss_value` 与 `per_budget_active_rate`，**不落 pairwise 字段**；来自 `last_step_snapshot`（单步快照，非轮均值） |
| `tools/ch3_ft_entity_stratified_sampler.py` | 173–202 | 正实体**不放回轮转**（每实体被抽次数几乎精确相等）；负实体每步 `rng.choice(pool, 64, replace=False)` 均匀不放回 |
| `configs/ch3-ft-c01-entity-ranking-cuda-formal-v1.json` | mechanism.entity_ranking | budgets=[121,…,9706]（LSPR23 N_pop=121336 投影）、n_pos=2、n_neg=64、xi_learning_rate=1e-4（evidence 自述「宿主接线阶段的实现判断……若观察到 xi 轨迹不稳定需要另行调整」） |

### 本地运行制品（只读核验，非新实验）

运行目录：`thesis/experiments/llm_probe/runs/diagnostics/ch3-ft-c01-entity-ranking-cuda-formal-v1/`

| 制品 | 核验内容 | 结果 |
| --- | --- | --- |
| `receipts/entity-ranking-diagnostics-{1,5,10,15,17,20}.json` | 六档激活率 | 与任务转述表**逐位一致**；确认字段来自 `last_step_snapshot`（单步，分辨率 1/128=0.0078125），每轮 `step_count=1000`，共 20 轮 |
| 同上（epoch 1/5/10/15/17/20） | 排序损失值 | 2.578 → 0.2402 → 0.1377 → 0.006308 → 0.008080 → 0.005191（分布坍缩 ~500 倍） |
| 同上 | `grad_norm_rank_median` | 457.3 → 2.692 → 0.02835 → 0.005860 → 0.001323 → 0.001549 |
| `checkpoints/inflight.pt` → `mechanism_state.cvar_threshold` | ξ 表 | 形状 (165,6)；col0(K=121)：min=0.01599362、median=0.02617806、mean=0.04823582、max=0.4287335；col4/col5 min 为 **负值**（−1.51e-6 / −6.59e-6） |
| `launch.log` | pairwise 字段 | 零命中——协作代理的「第 20 轮样本对损失上界 ≈1.57e-3」在本地制品不可复核 |

核验命令（miniconda rwkv 解释器，只读）：
```
/opt/miniconda3/envs/rwkv/bin/python -c "torch.load(.../inflight.pt, map_location='cpu')..."
# 逐列 min/median/mean/max 见上表
```

### 文献原件（本地全文）

- `raw/papers/methodology/ft-mechanisms/2022-Zhu-pAUC-DRO-ICML.pdf`
  （sha256=ce0c5e44…40，与 `wiki/papers/methodology/ft-mechanisms/2022-Zhu-pAUC-DRO低误报深度排序.md` 登记一致）。
  本轮直接读取物理第 4–6 页：
  - p.3 公式 (6)：CVaR 估计量 = top-(nγ) 平均，**要求 nγ 为整数**。
  - p.4 公式 (7) 下方原文假设 n₋β 为正整数；定理 1 给出变分形式
    min_s (1/n₊)Σᵢ [sᵢ + (1/β)ψᵢ]，ψᵢ = (1/n₋)Σⱼ(L−sᵢ)₊。
  - p.5 算法 1（SOPA）：s¹=0；步 4 p_ij=I(L−sᵢ>0)；步 5
    sᵢ ← sᵢ − (η₂/n₊)(1 − Σⱼp_ij/(β|B₋|))；步 6 ∇_t=(1/(β|B₊||B₋|))ΣΣ p_ij∇L。
  - p.6 定理 3：SOPA 迭代复杂度 T = O(1/(βε⁴))——**1/β 因子**。
  - 两阶段协议（CE 预训练→重置分类头→pAUC 微调）：wiki 笔记已核验为物理第 8 页。

## 关键推导核对（速查）

- K_eff(121) = 121×64/121336 = 0.0638228（= 收据键 0.06382277312586536 ✓）
- ∂L_rank/∂ξ_{p,K} = (1/(6·Np))·(1 − m/K_eff)，m = #{n: L_pn > ξ}
- 下行步（m=0）：1e-4/12 = **8.333e-6** ✓（转述值 8.33e-6）
- 上行/下行比（m=1，K=121 档）：1/K_eff − 1 = **14.669** ✓（转述值 14.7）
- 每实体被抽次数：2×20000/165 = **242.42** ✓（轮转采样 → 各实体几乎精确相等）
- 全程最大下行：242.42×8.333e-6 = **2.020e-3** ✓
- 2.020e-3 / col0 median(0.02617806) = **7.72%** ✓（转述的 7.7% 用的是**中位数**口径；若对 col0 min 则为 12.6%——转述文字把 min 与 7.7% 并置，口径需澄清）
- 0.01599362 / 1.57e-3 = 10.19 ✓（算术成立，但 1.57e-3 本地不可复核，见上）
- 驻点激活率（=β）：[0.000997, 0.004994, 0.009997, 0.019995, 0.039997, 0.079993]
- epoch20 实测单步激活数（×128）：[0,0,0,0,4,3]；col5 期望 10.24（3 快照累计 30.7 vs 实测 12，≈3.4σ 低）

## 过程检查点

- [x] 读损失模块全文（677 行）
- [x] 读宿主 `_ranking_phase` 与 ξ 更新
- [x] 读冻结配置 mechanism 块
- [x] 本地收据 6 轮核验
- [x] inflight.pt ξ 表独立核验
- [x] Zhu 2022 原件 p.4–6 直接读取（SOPA 精确形式）
- [x] 采样器抽样方式确认
- [x] 报告撰写 → `分析报告.md`
- [ ] 开放问题 1（总体分位数离线打分）——留待实验，本任务不执行
