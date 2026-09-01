# 调研笔记：BER 同框架机制一可行性

<!-- RESEARCH_ROUTE=RWKV -->

更新时间：2026-09-01（随做随写）

## 已读内部文档（证据等级：仓库内实测/规约文档）

| 文档 | 关键内容 |
| --- | --- |
| `2026-09-01-朱焱雷第三章机制组织与消融的完整理解.md`（提交 `07147ad`，工作树无此文件，经 `git show` 提取） | DS-RGO＝同一 Stackelberg 双层问题的内层约束集与外层全导数；交互项 `+3.80/+3.30`；差距＝本课题两机制无共享框架 |
| `2026-08-31-BER机制形式化与复杂度规约.md` | BER 全部公式；`S_e = max_t l`；R-U 变分形式；`ξ* = (1−β)` 分位数；活动集；水库 `B=4096`；推理参数 0；低档活动率 `[0,0,0,...]`；排序阶段前向为主要开销（C01 为 C00 的 2.4 倍） |
| `2026-08-31-CVaR预算失配数学分析/分析报告.md` | 驻点 `P(L>ξ*)=β`；稀有脉冲估计量（K=121 档期望 0.128 对/步）；SOPA 逐项对照（物理页 4–5）；c1/c2 修法 |
| `2026-08-31-CEM失败根因诊断.md` | 运行时状态机＋模型表示摘要＋固定容量＝死因；密度偏移 4.95 倍；「源年逐流 AP 差值不得持续为负」预注册断言 |
| `2026-08-31-两机制联动设计分析.md` | M-E 挂载点裁决；状态载体实测（`prior_flow_count` AUC 0.80 但漂移 3.8 倍）；四格梯度路径表 |
| `2026-08-31-M-E机制形式化与复杂度规约.md` | M-E 公式、参数量 `124,673`、消融臂 E1/E2 设计（嵌套子模型方法论可复用） |

## 本地文献索引命中（`--scope paper --mode hybrid`，索引 built_at 2026-09-01，stale=false）

查询式与命中（只列直接相关者）：

1. `"partial AUC pAUC distributionally robust optimization"`：
   - **Zhu 2022 pAUC-DRO**（`wiki/papers/methodology/ft-mechanisms/2022-Zhu-pAUC-DRO低误报深度排序.md`，全文核验，原件 sha256 `ce0c5e44…`）
     物理页 4 式(7)–(10)：顶部负样本选择写成 DRO，**CVaR 给精确非平滑估计、KL 正则给平滑软估计**——
     两种内层重加权对偶都在 BER 的机制来源论文里。
   - **Hu 2023 多示例双向部分 AUC**（`wiki/papers/methodology/ft-mechanisms/2023-Hu-多示例双向部分AUC.md`，全文核验，原件 sha256 `38542262…`，arXiv 2310.03234）
     物理页 8 式(8)–(9)：**袋级池化（均值/平滑最大/注意力）直接复合进双向 pAUC 目标**，
     即「聚合算子 ∘ pAUC」的耦合复合优化（FCCO）已发表。笔记明示「实体袋+pAUC 已被占用」。
2. `"multiple instance learning pooling max log-sum-exp attention bag"`：
   - **Ilse 2018 注意力 MIL**（全文核验笔记）：三步分解定理（页 2）；「均值适合算袋表示、不适合聚合实例分数」（页 3）；
     注意力池化相对均值增益量级 AUC +0.003~+0.028——参数化池化收益有限的校准数字。
   - **MIDAM（Zhu 2023 ICML）**（`wiki/papers/methodology/multiple-instance/2023-Zhu-MIDAM随机池化.md`，全文核验）：
     随机小包上的非线性池化不是完整包池化的无偏估计（物理页 4）；逐包移动状态修偏。
     对候选一的训练期截断袋（8192 流上限）适用同一警告。
   - **Gulcehre 2014 可学习范数池化**（全文核验笔记，页码齐全）：
     均值/RMS/最大池化＝归一化 Lp 范数在 p=1/2/∞ 的特例（式(3)页 3，3.2 节页 5）；
     最优 p 随数据集显著变化（表 1 页 12）；笔记已登记「在实体级聚合层换可学习 p」为待验证最小实验。
3. `"CVaR conditional value at risk quantile ranking"`：保形/风险控制类命中（CALIBURN、Bates 2021），
   与告警预算合同相关但不属本任务构造对象，未采用。

## 关键结构发现（设计推理，标注见报告）

- BER 的目标是**两层复合**：外层 CVaR_β（跨实体对）∘ softplus ∘ 内层聚合（实体内 max_t）。
  内层 max 本身就是一个内层优化（在单纯形顶点上取最优），
  即当前 C01 已经隐式是「聚合 ∘ CVaR-pAUC」复合结构，只是聚合被硬编码为 max。
- 因此表示/结构层与 BER 共享框架的**唯一天然槽位是实体聚合算子**：
  把 max 广义化为同族风险测度（CVaR_α／熵风险 LSE／Lp 范数），
  联合目标成为**嵌套风险测度／FCCO 实例**——与朱焱雷 DS-RGO「内层约束集×外层全导数」同构。
- 同片段跨流条件化违反严格过去性（任务约束 5）；逐实体运行时分位数草图是状态机（约束 2）；
  预算课程不在表示层；多预算多头破坏独立开关——这些方向均已排除，理由记入报告。

## 参数量约束的内部张力（须向主进程披露）

任务简报要求「参数量与 BER 同量级（约 10 万级）」，但 BER 推理参数实测为 **0**
（C01 与 C00 state_dict 逐位同形，`924,285` 元素）；朱焱雷的 DS 也是 0 参数（纯调度）。
候选一/二为 0～1 参数，字面满足「与 BER 同量级」，不满足括号里的 10 万级；
候选三（参数化读出注意力）可到 ~11 万但框架共享最弱。两种口径都如实报告。

## 制品搜查记录（2026-09-01 实测）

- 目标：源年验证集逐流 logits/分数制品（用于 CVaR_α 重聚合最小实测）。
- `runs/diagnostics/ch3-ft-c00-dual-selection-cuda-formal-v1/`：只有
  `checkpoints/{inflight,selected-by-entity,selected-by-flow}.pt` 与
  `receipts/{selection,split,input-transform}.json`。`selection.json` 的 `history`
  为轮级聚合指标（`validation_flow_ap`、`validation_entity_ap` 等），**无逐流分数**。
- `rg --no-ignore` 搜 `by-entity|per_entity_scores|entity_scores`（排除 lspr24/target）无源年命中。
- **结论：重聚合实测无法离线完成**，登记为报告的第一证伪实验（源年打分转储＋重聚合，无需训练）。

## 最小实验记录（2026-09-01，本机 miniconda rwkv，torch 2.12.0，CPU）

脚本：本目录 `cvar_agg_probe.py`、`atk_agg_probe.py`（自会话临时目录复制归档）。

### 实验 1：R-U 形式（detach 批内分位数 ζ）实现——发现真缺陷

命令：`/opt/miniconda3/envs/rwkv/bin/python cvar_agg_probe.py`，实测输出：

- 袋大小 `[200,150,100,60,20,5]`、`α=0.05` 时梯度支撑 `[9,7,4,2,0,0]`。
- **`αm ≤ 1` 的小袋（m=20、5）梯度支撑为 0**：ζ＝批最大值 ⇒ 所有 hinge 为零 ⇒ 无梯度，
  比 max（支撑 1）更糟——与 BER 分析否决「逐步取批内第 ⌈K_eff⌉ 大值」的退化同型。
- `αm` 非整数时（m=150）R-U 估计值与 top-k 均值有差（1.8587 vs 1.8445），整数档逐位一致。

### 实验 2：ATk（top-⌈αm⌉ 均值）静态实现——三项全过

命令：`/opt/miniconda3/envs/rwkv/bin/python atk_agg_probe.py`，实测输出：

- 值与逐实体显式 `topk(...).mean()` 逐位一致（`allclose atol=1e-6` 为真）。
- 梯度支撑 `[10,8,5,3,1,1]` ＝ 理论 `ceil(αm)∨1`，**小袋连续退化为 max**，无零梯度死角。
- `torch._dynamo.explain`：`graph_break_count = 0`、`graph_count = 1`；
  `torch.compile(fullgraph=True)` 编译执行成功，换形状二次调用成功。
- 实现要点：`sort(降序) + arange<k 权重矩阵`，无 `topk(k=张量)`、无布尔索引，全静态形状。
- 边界：玩具规模（E=6）、CPU inductor；宿主集成与 CUDA 下须复核，标待验证。

## 外部检索（摘要级候选，未入库，不得支撑正文论断）

- Fan, Lyu, Ying, Hu, "Learning with Average Top-k Loss", NeurIPS 2017（arXiv:1705.08826）：
  ATk 聚合损失＝均值与最大值的插值，R-U 重写式 `min_λ λ + (1/k)Σ[ℓ−λ]_+`。
- "Sum of Ranked Range Loss"（arXiv:2106.03300）：显式给出 top-k 均值＝`α=k/n` 的 CVaR。
- top-k 均值作 MIL 袋聚合已发表：Multi-Instance Multi-Scale CNN（arXiv:1907.02413）、
  ISPSCL（arXiv:2210.09452，"mean of the top-M ranked instance-level predictions"）；
  分位数聚合（arXiv:1806.05083）。
- 上述候选若需晋级为正文证据，按 `raw/`→`wiki/` 全文入库工作流处理。
