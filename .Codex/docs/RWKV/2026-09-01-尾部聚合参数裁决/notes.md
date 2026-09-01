# 尾部聚合参数裁决 notes（过程证据）

<!-- RESEARCH_ROUTE=RWKV -->

日期：2026-09-01。环境：本机 miniconda `rwkv`（`/opt/miniconda3/envs/rwkv/bin/python`，
torch `2.12.0`、numpy `2.4.6`，CPU，不占 GPU、不连服务器）。全程零 LSPR24 读取，零标签读取
（`y23.npy` 未加载）。

## 已读材料

| 材料 | 用途 |
| --- | --- |
| `2026-09-01-实体内尾部聚合先导诊断.md` 第六至八节 | 分层表、三条限制、α 地位声明 |
| `2026-09-01-BER同框架机制一可行性/调研报告.md` | 候选设计、ATk 实测、LSE 变体、变体 1b |
| `2026-08-31-BER机制形式化与复杂度规约.md` | 冻结预算 `[121,606,1213,2426,4853,9706]`、`N_- = 121336`、R-U 形式 |
| `tools/ch3_ft_entity_ranking_loss.py` 第 64–118 行 | 现有 max 实现（argmax+gather 确定性子梯度） |
| 本地 `runs/diagnostics/ch3-ft-entity-tail-aggregation-probe-v1/probe.json` | 结构统计锚点（非 AP 读数） |

## 实验 1：袋分布精确复算 + 路径 B 退化率（脚本 `bag_dist_path_b.py`）

命令：`/opt/miniconda3/envs/rwkv/bin/python bag_dist_path_b.py`
（脚本已随本目录归档；原运行于会话临时目录）

方法：逐字复刻 `ch3_ft_transformer_field_token_protocol_a.source_split`
（seed=42、validation_fraction=0.1、time_tail_fraction=0.15，参数取自
`configs/ch3-ft-transformer-field-token-protocol-a-seed42-v1.json`，经
`ch3-ft-c00-dual-selection-cuda-formal-v1.json` 的 `base.config_path` 指认），
只读 `E23/T23/M23`，有效流按 `M23[:, :128] > 0.5` 计。

核验：切分统计与冻结身份逐项相等（150680/208598/22444/0）；与 probe.json 的
**16 个结构锚点全部一致**（scored_flows=1238500、scored_entities=13529、中位数 2.0、
四分层计数 6290/5919/874/446、七个 α 档 k>1 计数、α=0.05 的 max_k=22407）。
验证最大袋 m_max=448128；训练侧实体 121501、流 11991315、中位袋 2.0、最大袋 2129920。

路径 B 核心读数（k = max(1, ⌈β·m⌉)，β = K/121336）：

| K | β | k>1 需 m≥ | 验证 k>1 | 占比 | 训练(截8192) k>1 | 占比 | 训练 mean_k |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 121 | 0.000997 | 1003 | 110 | 0.81% | 857 | 0.71% | 1.020 |
| 606 | 0.004994 | 201 | 332 | 2.45% | 2477 | 2.04% | 1.133 |
| 1213 | 0.009997 | 101 | 446 | 3.30% | 3587 | 2.95% | 1.285 |
| 2426 | 0.019994 | 51 | 583 | 4.31% | 4868 | 4.01% | 1.594 |
| 4853 | 0.039996 | 26 | 786 | 5.81% | 6661 | 5.48% | 2.219 |
| 9706 | 0.079993 | 13 | 1117 | 8.26% | 9824 | 8.09% | 3.487 |

路径 A 对照（同脚本）：α=0.5 时验证 k>1 实体 4279（31.63%）、mean_k 46.090
（与 probe.json 记录 46.08995 一致）；训练截断袋 k>1 39108（32.19%）、mean_k 17.154；
**α∈{0.25, 1/3, 0.5} 下 m≥2 饱和为均值的实体数均为 0**。
验证袋分位数 P50/P75/P90/P95/P99 = 2/3/9/35/675.76；训练袋 = 2/3/9/30/511。

## 实验 2：LSE 软聚合数值核验（脚本 `lse_path_c_probe.py`）

命令：`/opt/miniconda3/envs/rwkv/bin/python lse_path_c_probe.py`，全部断言通过：

- 极限：τ=1e4 时 |S−max|=6.91e-04 恰等于理论界 log(1000)/τ；τ=1e-4 时 |S−mean|=4.51e-04。
- 稳定性：logit 幅度 {1,30,100} × τ {1e-3,1,1e3} 九格，值与 dS/dl、dS/dρ 全部有限
  （max-shift 后 logsumexp 无溢出）。
- τ 梯度闭式对拍：dS/dτ = (Σw_i l_i − S)/τ = KL(w‖unif)/τ²，与 autograd 相对差 ≤ 2.5e-14
  （九个 τ 档）。量级：τ→0 趋于 Var/2（实测 4.4699 对 4.4702）；
  τ=1: 3.63，τ=10: 6.57e-2，τ=100: 6.91e-4，τ=1000: 6.91e-6——**大 τ 侧梯度平台
  按 KL_max/τ² ≤ log(m)/τ² 衰减，初始化偏大会失去学习信号**。
- 尺度耦合恒等式：|S_τ(c·l) − c·S_{cτ}(l)| ≤ 4.44e-16（c=2.5，三个 τ 档）——
  **跨年 logit 尺度漂移与 τ 漂移精确等价**。
- gradcheck(l, ρ) 双精度通过。
- 权重泄漏（m=1000、logit 尺度 3）：τ=0.5/1/2/5 的参与率 129.1/9.6/3.6/1.9 条流，
  τ≤1 时 1000/1000 条流权重 >1e-12——**权重弥散到整袋**。
- `torch._dynamo.explain` graph_break_count=0；`fullgraph=True` 编译执行成功、
  换形状二次调用成功、dρ 有限。参数量 1 个标量（τ=exp(ρ)）。

## 实验 3：路径 A 边界算术与 ATk 等变性（内联命令）

- 穷举 m∈[2,100000]：α=1/2 时 ⌈m/2⌉<m 全部成立；m=2 时 k=1（退化为 max）；
  任何 α>1/2 在 m=2 即 ⌈2α⌉=2=m（饱和为均值）。
- ATk 等变性：top-⌈m/2⌉ 选择集对正仿射变换 c·l+b（c=3.7,b=−2.2）不变，
  均值满足 ATk(c·l+b)=c·ATk(l)+b（|误差|<1e-12）——聚合语义对跨年 logit 尺度漂移免疫。

## 文献状态

- `status --json`：索引在线（1497 条笔记，papers 536），未见 stale 告警。
- 调研报告引用的四篇全文笔记均在库：
  `wiki/papers/methodology/2014-Gulcehre-可学习范数池化Lp单元.md`、
  `wiki/papers/methodology/ft-mechanisms/2022-Zhu-pAUC-DRO低误报深度排序.md`、
  `wiki/papers/methodology/ft-mechanisms/2023-Hu-多示例双向部分AUC.md`、
  `wiki/papers/methodology/multiple-instance/2023-Zhu-MIDAM随机池化.md`。
- 一次 `--scope paper --mode hybrid` 主题查询（top-k/CVaR 袋聚合）最高命中为 QUIC
  数据集笔记，与本题无关——本地库中除上述四篇外无更近的聚合参数选值文献；
  ATk 原文（Fan 2017）仍为［摘要级］，其 k 由验证集调参、无推荐定值。

## 约束遵守自检

- 未使用先导任何 α→AP 读数选值（效应量、峰值位置、分层 AP 均未进入推导）；
  先导仅以「八个 α 方向一致」的资格作方向证据。
- 未读 LSPR24；未读 y23；未连服务器；未占 GPU。
- 全部数值验证命令与精确结果已在上文与两份脚本中登记。
