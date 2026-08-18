# 任务方案册：LSPR23 到 LSPR24 跨年度泛化

- **日期**：2026-08-12
- **路线**：`RESEARCH_ROUTE=RWKV`
- **任务状态**：候选均为**实验待证**；本方案册只冻结种子 42 快速筛选合同，不宣称方法有效
- **当前 P0**：稀有恶意质量保护的非对称部分最优传输与无标签负迁移停机/回滚
- **文献综合代理**：`gpt-5.6-sol`，`effort=max`
- **实施边界**：本文件可直接交给一个实现代理；本轮文献任务不实现代码、不启动实验

## 1. 直接结论

跨年度任务固定为 **LSPR23 有标签训练到 LSPR24 无标签前缀适应与目标评价**。这不表示整篇论文只能使用一个数据集；它只裁决本跨年度任务。当前已停止其他单年度任务，本方案册不为它们定义数据合同。

真实种子 42 结果显示，共享 XGBoost 的目标开发 PR-AUC 为 `0.038902589823969644`，显著高于一维卷积网络 `0.0176996`、候选 B 最佳离散 RWKV `0.01920596`、C12 最佳 K-DELTA `0.01697728`、R1 最佳 GroupDRO `0.0128779`。候选 B 的角色分离物理时间变体仅为 `0.01012302`，C12-R 六格均不超过 `0.00927448` 且源阈值恶意召回全为 `0`。因此下一实验必须保留 XGBoost 强排序锚，先修复跨年可迁移表示和排序；不得继续在弱序列排序器上叠加时间衰减、阈值、门控或回退。

候选优先级冻结为：

1. **P0：稀有恶意质量保护的非对称部分最优传输 + 无标签负迁移停机/回滚**。
2. **P1：XGBoost 叶/分数强锚 + 有界 RWKV 残差**。
3. **P2：源恶意方向保护的无标签谱分类头修正**；只有非单调改变排序时才保留。

普通 DANN、CORAL、MMD、全量或普通部分最优传输、普通测试时适应、单调校准都只是先例或基线，不是原创。P0 的贡献边界只允许落在四者的任务特定组合：**有标签源恶意质量下限、源/目标非对称支持拒绝、XGBoost 叶/分数锚、仅用目标前缀的无标签停机与回滚**。

## 2. 不可变数据与评价合同

### 2.1 四角色

| 角色 | 时间范围 | 训练/适应权限 | 标签权限 |
| --- | --- | --- | --- |
| `source-train` | LSPR23 活动秒前 80% | 拟合字段变换、XGBoost、源原型和候选参数 | 训练器可见 |
| `source-validation` | LSPR23 活动秒后 20% | 冻结超参数、构造源域伪迁移与有害适应门禁校准 | 只用于源域选型与阈值，不更新字段变换 |
| `target-prefix` | LSPR24 最早 10% 活动秒 | 仅无标签拟合目标原型、传输计划和门禁诊断 | 对训练器、适应器和评价器均不可见 |
| `target-development` | LSPR24 随后 70% | 只生成冻结预测；五变体概率全部封存后一次性评价 | 只允许独立评价器在封存后读取 |
| `final-test` | LSPR24 最后 20% | 当前完全禁入 | 禁止读取、统计、哈希、持久化或推断成员 |

开发实验必须维持 `final_accessed=false`。目标开发标签不得用于损失、超参数、传输质量、原型数、成本权重、停机、回滚、阈值或早停。若发生任一项，整个运行标为**实验无效**，而不是性能失败。

### 2.2 输入合同

- 只消费既有 `lspr-crossyear-python-cache-v1`，固定 `x_value[77] + x_missing[77] + log1p(delta_t_us)` 共 155 维。
- 读取器必须按清单发现制品并核验哈希。禁止扫描原始 LSPR23 CSV 或 LSPR24 Parquet 重新造候选专属数据。
- `Flow ID`、IP、端口、服务、主机、网段、演习身份、年份、角色、路径、样本/序列/分组键、标签及任何代理变量均不得进入模型。
- `sample_id`、2-IP 组键、序列位置只用于封存、去重、顺序和评价连接；不得进入 XGBoost、距离或传输成本。
- 目标开发推理不更新原型、耦合、阈值或门禁；只应用在 `target-prefix` 结束时冻结的适配器。

### 2.3 只读共享输入

远端项目根以当前路线合同核验为准。相对实验工程根的只读输入为：

```text
runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/
  dataset-manifest.json
  receipts/materialization.json
  receipts/final-isolation.json
  experiments/c12-seed42-q0-2ip-v1/
    experiment-manifest.json
    selection-receipt.json
    sample-manifest.parquet
    sequence-manifest.parquet
    python-cache-v1/cache-manifest.json

runs/baselines/lspr-crossyear-tabular-q0-seed42-v2/xgboost/
  target_development_probability.npy
  probability_seal.json
  metrics.json
  run_state.json

runs/baselines/lspr-baseline-dual-track-q0-seed42-v1/
  track-b/dijk2026_xgboost/
  track-b/leoste_1d_cnn_nearest_text/
```

其中第一组是唯一数据入口；第二组是已成功 Q0 v2 的共享 CPU XGBoost `0.038902589823969644` 目标开发锚概率与封存/指标/状态收据；第三组只提供强基线对照。旧 `runs/baselines/lspr-crossyear-tabular-q0-seed42-v1` 因二次复杂度阈值扫描被主动中止，**禁止发现、复用或作为锚**。v2 目录没有可复用的目标前缀概率、叶表示或持久 XGBoost 模型，因此只能提供固定的历史绝对门槛和样本顺序收据，不能参与目标前缀适应、停机或叶成本构造，也不能要求不同执行设备产生逐点完全相同的概率。实施前必须只读核实 v2 的 `run_state.json` 成功状态、`probability_seal.json`、模式、哈希、行数和 `final_accessed=false`；若远端实际制品不能由上述 v2 成功收据发现，即停止并报告阻塞，禁止回退 v1、猜测文件名或复制数据。

## 3. P0 冻结科学合同

### 3.1 研究假设

跨年支持不重叠和恶意低基率会使普通全量 OT 或无约束 POT 优先搬运占多数的良性质量，从而得到更小的传输代价却破坏恶意排序。P0 检验两个可独立证伪的机制：

- **M1：稀有恶意质量保护的非对称部分传输**。允许拒绝不受支持的源/目标质量，但要求传输计划保留最低源恶意质量，并只对 XGBoost 的局部排序作有界修正。
- **M2：无标签负迁移停机/回滚**。只观察耦合可行性、源恶意有效样本量、目标前缀分半稳定性和相对 XGBoost 的排序扰动；诊断异常时输出原始 XGBoost 分数。

M1 负责产生可能的排序增益，M2 负责限制伤害。自然目标上 `M1+M2` 与 M1 完全相同是允许结果；M2 的独立贡献必须在预注册有害适应网格中评价，不能强求其在安全运行上额外提高 PR-AUC。

### 3.2 XGBoost 强锚与表示

以共享 XGBoost 的冻结概率 `p_0(x)` 为最终锚，记裁剪后的对数几率为

$$
z_0(x)=\operatorname{logit}(\operatorname{clip}(p_0(x),10^{-6},1-10^{-6})).
$$

候选入口按共享生产参数在 `source-train` 确定性重拟合 XGBoost，用于提取每棵树的叶编号和四角色分数。设备固定为 `tree_method="hist", device="cuda"`；除设备外，树数、深度、学习率、行/列采样、正则、随机种子、样本成员和字段必须与共享锚完全一致。启动前先在源训练的确定性最小子集上真实拟合并预测，核验配置回读仍为 `cuda`、输出有限、叶编号可提取，并记录 GPU 型号、XGBoost/CUDA 版本、拟合/预测耗时和峰值显存。CUDA 不可用、配置未生效或出现回退警告时停止并写阻塞收据，禁止静默回退 CPU。

GPU 重拟合的 `target-development` 概率必须在**不打开目标标签**的条件下封存，并与既有共享 CPU 锚核对样本数、顺序哈希、数据清单哈希和有限值。CPU/GPU 后端的概率相关性与最大绝对差只作为复现诊断，不作为失败门禁。所有五个变体必须共享同一个 GPU XGBoost 模型、叶表示和原始概率；封存完成后一次性连接目标开发标签，先得到同轮 GPU 锚指标，再进行候选比较。整体晋级必须同时满足“相对同轮 GPU 锚提高至少 `0.005`”和“绝对 PR-AUC 至少 `0.043902589823969644`”；共享 CPU XGBoost 的 `0.038902589823969644` 只作为不可降低的历史绝对基准，不用不同设备的逐点概率一致性替代公平性。

叶距离与分数距离为：

$$
d_{\mathrm{leaf}}(x,x')=\frac{1}{T}\sum_{t=1}^{T}\mathbf 1[\ell_t(x)\ne\ell_t(x')],\qquad
C_{ij}=0.75d_{\mathrm{leaf}}(s_i,t_j)+0.25\frac{|z_0(s_i)-z_0(t_j)|}{q_{0.95}+10^{-6}},
$$

其中 `q_0.95` 只由 `source-train` 成对分数差估计。成本权重、裁剪和距离尺度均不得用 LSPR24 标签选择。

为保证 RTX 5090 可运行，源原型固定为每类分层聚类：恶意最多 128 个、良性最多 512 个；目标前缀最多 1024 个原型。原型权重保持其代表的原始样本质量，不做 1:1 类平衡伪造。原型数只可在 LSPR23 源验证伪迁移中裁决，目标开发后不得改变。

### 3.3 M1：恶意质量保护的非对称部分传输

令源、目标前缀原型质量分别为 $a,b$，源训练恶意先验为 $\pi_s^+$。传输计划求解：

$$
\begin{aligned}
\min_{\Pi\ge 0,\xi_+\ge 0}\quad
&\langle C,\Pi\rangle+\varepsilon H(\Pi)
+\tau_s\mathrm{KL}(\Pi\mathbf 1\Vert a)
+\tau_t\mathrm{KL}(\Pi^\top\mathbf 1\Vert b)+\lambda_\xi\xi_+\\
\text{s.t.}\quad
&\mathbf 1^\top\Pi\mathbf 1=m,\\
&\sum_{i:y_i=1}(\Pi\mathbf 1)_i\ge \rho_+\pi_s^+-\xi_+.
\end{aligned}
$$

`H` 为负熵。`m<1` 允许支持拒绝；`tau_s>tau_t` 使目标私有/污染质量更容易不参与匹配；恶意质量下限防止最小成本计划把稀有恶意源质量全部丢弃。P0 不照搬任何论文数值，参数只按下述 LSPR23 源域伪迁移冻结：

- 原型规模：恶意 128、良性 512、目标 1024；不足时使用全部非空原型。
- 搜索网格：`m ∈ {0.6, 0.8}`、`epsilon ∈ {0.03, 0.10}`、`tau_s/tau_t ∈ {2, 4}`、`rho_plus ∈ {0.5, 0.8}`。
- 选择数据：仅 LSPR23 `source-validation` 的按时间前半伪前缀与后半伪开发；再做四个连续时间块轮换。
- 选择规则：先排除恶意质量松弛超过要求质量 5% 的配置，再最大化四轮伪迁移 PR-AUC 中位数；并列时取预算召回最坏值较高者，再并列取更小 `m`、更大熵正则的低复杂度配置。
- 以上唯一胜出配置在读取 LSPR24 前写入 `source-only-selection.json` 并哈希冻结。不得以目标前缀无标签分数重新排名多个配置；目标前缀只能触发 M2 的通过或回滚。

目标前缀原型 $j$ 的传输恶意概率、支持度和局部修正为：

$$
q_j=\sum_i\Pi_{ij},\quad
\hat p_j^+=\frac{\sum_{i:y_i=1}\Pi_{ij}}{q_j+10^{-12}},\quad
u_j=\min\left(1,\frac{q_j}{b_j+10^{-12}}\right),
$$

$$
\delta_j=\operatorname{clip}\left(\operatorname{logit}(\hat p_j^+)-\bar z_{0,j},-\log 4,\log 4\right).
$$

冻结后，目标开发样本只关联到最近且在源校准支持半径内的目标前缀原型 $j(x)$：

$$
z_{M1}(x)=z_0(x)+0.5u_{j(x)}\delta_{j(x)}.
$$

无支持或超出半径时令修正为零。不同原型的修正不同，因此允许改变排序；若输出只是 $z_0$ 的全局单调变换，P0 立即否决。

### 3.4 M2：无标签停机与回滚

M2 的阈值只从上述 LSPR23 四轮伪迁移冻结。每轮同时生成有害适应：移除恶意质量下限、交换 `tau_s/tau_t`、使用 `m=1` 全量传输、把修正幅度放大到 `2log4`。已知源验证标签只用于标记某配置是否使 PR-AUC 相对 XGBoost 下降至少 `0.003`；进入 LSPR24 后门禁输入不含标签。

门禁观测量为：

1. 恶意质量松弛占要求质量的比例 `slack_ratio`。
2. 源恶意传输边缘的有效原型数 $(\sum w_i)^2/\sum w_i^2$。
3. 目标未匹配质量与最大单原型耦合集中度。
4. 用目标前缀前半/后半分别拟合的修正，在对方半区上的 Spearman 一致性和三个固定预算 Top-K Jaccard。
5. 修正相对锚的对数几率 95/99 分位、排序翻转率和三个预算的候选集合替换率。

每个连续观测量的通过区间取 LSPR23 **无害**伪迁移的 5%–95% 包络；此外硬要求 `slack_ratio≤0.05`、恶意有效原型数至少 8。M2 只有在全部条件通过时取 `z_M1`，否则逐样本完整回滚到 `z_0`。门禁规则和包络写入 `source-only-gate.json` 后才能读取目标前缀。

M2 不得使用目标预测类别均衡性作为单独通过依据。迁移分数、EnsV 一致性或预测互信息可以记录为诊断，但稀有恶意任务中多数类共识可能掩盖排序崩塌，不能覆盖上述硬条件。

## 4. P0 五变体与独立消融

所有变体共享同一 XGBoost、原型、源域选择预算、目标前缀和目标开发成员：

| 键 | 展示名 | 目的 |
| --- | --- | --- |
| `B0_XGB_ANCHOR` | 共享 XGBoost 强锚 | 精确复现 `0.038902589823969644`；不重选基线 |
| `U1_FULL_OT` | 全量对称最优传输 | 证明普通全量 OT 在支持错配下是否负迁移 |
| `U2_ASYM_POT_NO_FLOOR` | 非对称部分传输但无恶意质量下限 | 独立消融恶意质量保护 |
| `M1_PROTECTED_ASYM_POT` | 恶意质量保护的非对称部分传输 | 检验排序生成机制 M1 |
| `M1_M2_SAFE_ROLLBACK` | M1 加无标签停机/回滚 | 检验自然目标安全输出与 M2 |

另在 LSPR23 伪迁移中报告 `M1_SYMMETRIC`（令 `tau_s=tau_t`）以分离非对称性。它不新增一次目标开发调参机会；其目标开发概率可同批封存作诊断，但不得据结果改主配置。

## 5. 强基线与评价指标

### 5.1 强基线

- 主晋级锚：共享 XGBoost `0.038902589823969644`。
- 协议近邻：Dijk 约束 XGBoost `0.0368559`。
- 神经接收器：一维卷积网络 `0.0176996`、候选 B 离散 RWKV `0.01920596`。
- 已运行历史候选：K-DELTA `0.01697728`、C12-R `≤0.00927448`、GroupDRO `0.0128779`。
- 方法近邻：全量 OT、无保护非对称 POT；DANN/CORAL/MMD 只在已有可复用缓存且不扩大实现时作为附加基线，不得延迟 P0。

历史数字只用于候选排序，不冒充当前方法的有效性证据。P0 必须在同一成员上重新评价五变体；不得削弱 XGBoost 或只与神经弱基线比较。

### 5.2 必报指标与诊断

- 主指标：目标开发逐流 PR-AUC。
- 固定告警预算：每百万流 100、1000、10000 条告警的恶意召回；并列概率必须整组处理。
- 辅助：恶意类 F1、精确率、召回率、宏平均 F1、Brier、15 桶 ECE。
- 排序变化：与 XGBoost 的 Spearman、Top-K Jaccard、顺序翻转率、被提升/压低的样本数。
- 机制可观测量：传输总质量、恶意质量、松弛、未匹配质量、耦合熵、最大集中度、有效恶意原型数、支持外回滚率、M2 触发原因。
- 效率：训练/适应/推理墙钟、峰值主存、峰值显存、原型与耦合矩阵大小。

## 6. 种子 42 晋级、弱信号与否决门槛

### 6.1 P0 整体晋级

`M1_M2_SAFE_ROLLBACK` 同时满足以下条件才允许申请种子 42/43/44 正式验证：

1. PR-AUC 至少为 `0.043902589823969644`，且相对同轮 GPU XGBoost 锚至少提高 `0.005`。
2. 三个固定预算中至少两个召回不低于 XGBoost；任一预算下降不得超过 `0.002` 绝对值；至少一个预算提高 `0.005` 绝对值。
3. 目标开发标签只在全部候选概率和无标签门禁决定封存后连接，`final_accessed=false`。
4. 输出确实非单调改变排序；至少一个固定预算 Top-K 集合与锚不完全相同。

若 PR-AUC 严格高于锚但增量小于 `0.005`，只记为**弱正信号/不晋级**，最多允许依据已记录诊断重构一轮；不得读取目标开发后追参。

### 6.2 机制门槛

- M1 的质量保护相对 `U2_ASYM_POT_NO_FLOOR` 必须提高 PR-AUC 至少 `0.002`，且恶意质量松弛不超过要求质量的 5%。否则“恶意质量保护”不具独立实验贡献。
- 非对称版本相对 `M1_SYMMETRIC` 必须提高 PR-AUC 至少 `0.002`，或在 PR-AUC 不下降超过 `0.001` 时把支持外错误迁移/预算召回至少一项改善到预注册门槛；否则删去“非对称”主张。
- M2 在 LSPR23 有害适应网格中必须回滚至少 80% 的 `AP` 下降 `≥0.003` 情形，误回滚不超过 20%，且相对永不回滚把平均遗憾降低至少 50%。否则 M2 不进入完整方案。

### 6.3 立即否决或实验无效

- 完整方案 PR-AUC 不高于 XGBoost，或固定预算出现超门槛退化：Q0 不晋级。
- 恶意质量下限反复依赖大于 5% 的松弛、有效恶意原型少于 8、耦合由单一原型支配：M1 数学/数据条件不成立。
- 最终修正只是全局温度、阈值或其他单调变换：作为主创新淘汰。
- 使用目标前缀/开发标签、读取开发标签后选配置、访问最终 20%、锚样本顺序不一致、概率未先封存：实验无效，修复合同后重做，不计科学失败。
- 仅局部告警预算改善但 PR-AUC 下降：不得把纯决策校准包装成迁移主创新。

## 7. 实施交接包

### 7.1 建议独占文件边界

一个实现代理独占下列新文件，命名可在实现计划中一次性确认，但不得与其他代理共改：

```text
thesis/experiments/llm_probe/src/flow_probe/crossyear_protected_partial_ot.py
thesis/experiments/llm_probe/configs/crossyear-protected-asymmetric-pot-q0-seed42-v1.json
thesis/experiments/llm_probe/scripts/remote_launchers/run_crossyear_protected_asymmetric_pot_q0_seed42_v1.sh
.Codex/docs/RWKV/2026-08-12-跨年度恶意质量保护部分传输-Q0实施与运行报告.md
```

若需要拆模块，只允许在 `src/flow_probe/crossyear_protected_partial_ot_*.py` 新增候选专属文件，并在实施计划先列全。不得修改共享加载器来迁就候选；优先只读导入其公开接口或在候选模块内做严格适配。

### 7.2 不得修改的共享文件

```text
.Codex/docs/RWKV/RWKV路线总控.md
.Codex/docs/RWKV/RWKV当前恢复卡.md
.Codex/docs/RWKV/2026-08-08-第三章候选方案登记册.md
.Codex/docs/RWKV/2026-08-11-LSPR23-LSPR24共同字段审计与跨年度数据合同.md
thesis/experiments/llm_probe/src/flow_probe/lspr_crossyear_dataset.py
thesis/experiments/llm_probe/src/flow_probe/lspr_crossyear_tabular_baselines.py
thesis/experiments/llm_probe/src/flow_probe/lspr_baseline_matrix_train.py
thesis/experiments/llm_probe/configs/lspr-crossyear-c12-seed42-q0-v1.json
thesis/experiments/llm_probe/configs/lspr-baseline-matrix-track-b-q0-seed42-v1.json
thesis/experiments/llm_probe/scripts/remote_launchers/run_lspr_baseline_matrix_q0_seed42_v1.sh
```

不得覆盖、回滚、暂存或清理他人变更。权威总控、恢复卡与登记册由根主进程在真实实验后统一更新。

### 7.3 独立运行身份

```text
运行根：runs/candidates/crossyear-rare-mass-protected-asymmetric-pot-q0-seed42-v1/
持久会话：crossyear-protected-pot-q0-s42-v1
SwanLab 工作区/项目：mortiswang/malicious-traffic-llm
```

SwanLab 运行名必须逐变体唯一：

```text
crossyear-tl1-xgb-anchor-seed42
crossyear-tl1-full-ot-seed42
crossyear-tl1-asym-pot-no-floor-seed42
crossyear-tl1-protected-asym-pot-seed42
crossyear-tl1-protected-asym-pot-gated-seed42
```

启动器必须在读取数据或创建云端运行前机械断言当前授权工作区/项目与配置一致。远端服务器、GPU、凭据变量和项目根必须以启动时路线状态重新核验，不沿用历史进程假设。

### 7.4 阶段入口

1. **G0 只读预检**：核验机器、项目根、磁盘/内存/GPU、依赖、缓存/基线清单哈希、目标标签权限、已有同名运行和 `final_accessed=false`；以 `tree_method="hist", device="cuda"` 完成 XGBoost 最小真实拟合/预测与设备生效收据，禁止 CPU 回退。
2. **Q0-A 源域冻结**：重拟合 XGBoost、核对锚概率、建立源原型、完成 LSPR23 伪迁移参数选择与 M2 包络；发布 `source-only-selection.json`、`source-only-gate.json`。
3. **Q0-B 无标签适应与封存**：只读目标前缀，冻结目标原型和耦合；为所有变体生成目标开发概率、门禁决定、样本顺序与哈希。此阶段标签侧车保持未打开。
4. **Q0-C 单次评价**：所有变体封存收据通过后，评价器一次性连接目标开发标签，输出共同指标、预算召回和机制消融。
5. **Q0-D 裁决**：机械应用第 6 节门槛；输出 `不晋级`、`弱正信号/不晋级` 或 `申请多种子正式验证`。任何结果仍是 Q0 筛选证据。

### 7.5 最小验收命令

实现后在实验工程根执行；以下命令只定义验收，不授权本轮文献代理运行实验：

```bash
UV_CACHE_DIR=/tmp/crossyear-pot-uv PYTHONPYCACHEPREFIX=/tmp/crossyear-pot-pyc \
  uv run --no-sync python -m py_compile \
  src/flow_probe/crossyear_protected_partial_ot.py

PYTHONPATH=src uv run --no-sync python \
  -m flow_probe.crossyear_protected_partial_ot audit \
  --config configs/crossyear-protected-asymmetric-pot-q0-seed42-v1.json \
  --cache-root runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/experiments/c12-seed42-q0-2ip-v1/python-cache-v1

bash -n scripts/remote_launchers/run_crossyear_protected_asymmetric_pot_q0_seed42_v1.sh

bash scripts/remote_launchers/run_crossyear_protected_asymmetric_pot_q0_seed42_v1.sh
```

运行后至少机械核验：

```bash
jq -e '.state == "finished" and .exit_code == 0 and .final_accessed == false' \
  runs/candidates/crossyear-rare-mass-protected-asymmetric-pot-q0-seed42-v1/status.json

jq -e '.target_labels_used_for_tuning == false and .target_labels_opened_after_all_probability_seals == true and .final_accessed == false' \
  runs/candidates/crossyear-rare-mass-protected-asymmetric-pot-q0-seed42-v1/decision.json
```

应保留 `launcher.log`、`status.json`、`resource-plan.json`、输入/配置/源码哈希、源选择与门禁收据、原型/耦合诊断、逐变体概率及封存、指标、SwanLab 身份、退出码和最终 `decision.json`。已有非空运行根必须拒绝覆盖；只有带成功收据的同身份运行允许幂等跳过。

### 7.6 阻塞条件

- 只读缓存、锚概率、封存收据或哈希缺失；`final_accessed` 不是 `false`。
- GPU XGBoost 最小真实拟合/预测失败、配置回读不为 CUDA、出现静默 CPU 回退，或重拟合概率与共享 CPU 收据的样本数、顺序哈希、数据清单哈希不一致。
- 目标前缀标签能被训练器发现，或目标开发标签在全部概率封存前可被打开。
- OT 求解器不收敛、恶意质量约束只能靠超 5% 松弛满足、有效恶意原型不足 8。
- 正式环境缺少锁定依赖；不得静默更换 OT 求解器、XGBoost 或回退 CPU/GPU 实现。
- 预计扫描超过 500 万行、内存超过 8 GiB 或墙钟超过 30 分钟时必须在服务器运行；RTX 5090 空闲显存不足 8 GiB 时停止 GPU 路径，不静默回退。资源收据必须包含设备、驱动/CUDA、XGBoost 版本、峰值显存和分阶段耗时。
- SwanLab 授权目的地不一致、服务器离线、磁盘可用不足 10 GiB或达到 80% 使用率时停止并保留阻塞收据；这些不计科学失败。

## 8. P1：XGBoost 强锚加有界 RWKV 残差

### 理论与缺陷响应

P1 不让 RWKV 取代强树排序，而令其只学习交叉拟合 XGBoost 的近零残差：

$$
z(x_t)=z_0(x_t)+\alpha_tB\tanh(r_\theta(e_{\mathrm{leaf},t},z_{0,t})/B).
$$

M1 是“叶表示/分数锚 + RWKV 残差”；M2 是幅度和顺序翻转信任域。源高间隔样本对使用排序保持损失，只有锚近并列样本允许较多翻转。目标前缀只允许无标签一致性确定 `alpha_t`，不使用物理时间或频率分支。

### 最小快速实验

- XGBoost；独立 RWKV；XGBoost+无界残差；XGBoost+有界残差；完整信任域；序列打乱诊断。
- 整体门槛同 P0：PR-AUC 至少 `0.043902589823969644` 且预算不退化。
- M1 相对 XGBoost 至少 `+0.005`；M2 相对无界残差至少保护 `0.002` PR-AUC 或显著减少高间隔错误翻转，且自身 PR-AUC 不下降超过 `0.001`。
- 序列打乱若完全不影响结果，RWKV 序列机制无独立证据；可降级为叶残差多层感知机，不得保留 RWKV 主张。

### 原创与重复边界

树叶嵌入、神经残差、RWKV、排序约束均非原创。可能的任务特定贡献只在“跨年度稀有恶意排序中，以强树为主预测器、RWKV 仅修改近并列局部排序并受可审计翻转预算约束”。它不同于候选 B 的物理时间/频谱状态，不使用 C12 的目标状态更新或阈值回退，也不同于 R1 的最坏环境风险目标。

RTX 5090 种子 42 预计 8–12 GiB 显存、8–16 GPU 小时（含五变体）；在 P0 无信号前不实施。

## 9. P2：源恶意方向保护的无标签谱分类头修正

### 理论与缺陷响应

先以 XGBoost 叶稀疏表示拟合线性代理头 $w$，硬门禁要求其源验证排序和目标无标签排序与 XGBoost 高保真。M1 采用目标前缀预测的低秩谱约束，M2 保护源恶意—困难良性样本对方向：

$$
\min_w L_s(w)+\lambda_T\|(I-U_kU_k^\top)\Phi_tw\|_2^2
+\lambda_+\sum_{(i,j)\in\mathcal H_+}[\gamma-(w^\top\phi_i-w^\top\phi_j)]_+.
$$

秩、正则强度和困难对只由 LSPR23 伪迁移预注册。目标标签不能用于论文原方法中常见的超参数选择。

### 最小快速实验与门槛

- XGBoost；叶线性代理；仅谱约束；仅恶意方向保持；完整组合；全局温度/单调校准负对照。
- 叶线性代理在源验证必须保持 XGBoost PR-AUC 的至少 98%，目标开发评价后若低于 XGBoost 的 90%，本路线直接停止。
- 完整组合整体门槛仍为 `0.043902589823969644`；两个机制各相对对应消融至少 `+0.002` PR-AUC。
- 若与 XGBoost 的排序完全相同或只改变阈值/校准，立即淘汰；纯单调校准不能成为主创新。

### 原创与重复边界

标签对齐正则、谱投影、线性头和成对排序损失均非原创。可能的独立边界仅是“无目标标签选择、保护源恶意困难方向、作用于 XGBoost 叶代理并要求非单调排序变化”。它不使用 C12-R 的双参照决策回放，也不以校准改善替代排序改善。

RTX 5090 种子 42 预计小于 4 GiB、2–4 小时；只有 P0、P1 均无晋级信号时实施。

## 10. 第三章理论深度与工作量映射

三个候选都能组织成朱焱雷第三章级论证，但不机械复制页数或公式：

| 章节构件 | P0 | P1 | P2 |
| --- | --- | --- | --- |
| 问题定义 | 低基率、支持不重叠、目标污染 | 强树与弱序列排序差距 | 目标谱与恶意方向冲突 |
| 两个独立机制 | 质量保护非对称 POT；无标签回滚 | 树锚残差；顺序信任域 | 目标谱头；恶意方向保持 |
| 理论族 | 部分/非平衡 OT、风险界、质量可行性 | 有界残差、排序扰动界 | 谱正则、成对排序间隔 |
| 算法 | 原型、耦合、外推、门禁 | 交叉拟合、残差训练、翻转预算 | 叶代理、谱分解、约束求解 |
| 必要消融 | 全量/无保护/对称/有无回滚 | 独立/无界/有界/打乱 | 代理/单机制/组合/单调负对照 |
| 失败分析 | 质量不可行、攻击支持反转 | 锚已饱和、残差过拟合 | 稀有方向落在谱尾、代理失真 |

P0 的章节工作量最大且理论独立性最清楚，优先实施。任何候选只有通过真实共同预算、多种子和困难分面实验后才可晋级为论文贡献；文献数量、公式完整度和方案册本身都不能替代实验。

## 11. 文献依据与开放问题

- POT/UOT 来源：Courty OT、PPOT、WARMPOT、BUOT；它们不提供本任务的源恶意质量下限与前缀回滚。
- 稀有类边界：PROTOCOL 已覆盖渐进 POT、非平衡类别边缘和少数类表示再平衡，所以“部分质量”或“少数类再平衡”本身不构成原创。
- 无标签选模：迁移分数与 EnsV 可提供诊断，但其类别均衡或多数预测共识在恶意低基率下可能失真。
- 表示/状态近邻：DANN、RAINCOAT、ACON、DI-NIDS、TTA-AD、RTTAD、CANDI、OWAD、SoTTA、FOIL、DIVERSIFY 已覆盖通用表示、时频与测试时适应；结合当前弱序列 Q0，不列为 P0。
- 谱头：标签对齐正则提供分类头适应起点，但原实验用目标标签选超参数，本任务必须改成源域预注册与无标签门禁。
- 标签移位：BBSE/JCPOT 可作诊断或附加基线；攻击族支持变化使纯标签移位假设不足。
- 因果路线：LCA 的可逆混合、无混杂、稀疏和充分环境变化假设在当前 Q0 尚无可观测支持，不优先实施完整模型。

ReCDA 的 KDD 2024 论文（DOI `10.1145/3637528.3672007`）及 2025 年 TDSC 扩展（DOI `10.1109/TDSC.2025.3599321`）目前只有正式摘要/元数据，未取得合法公开全文，不能用于方法细节或原创性裁决；待用户提供全文后再补核验，不阻塞 P0。

## 12. 实施者唯一下一动作

先把第 7.1 节四个独占文件写入持久化实施计划，读取 `daily-coding`、远程脚本合同和故障手册对应章节，再实现 **G0 审计 → Q0-A 源域冻结 → Q0-B 无标签封存 → Q0-C 单次评价 → Q0-D 机械裁决**。不得并行启动 P1/P2，不得重跑候选 B、C12、C12-R 或 R1，不得修改本方案册列出的共享文件。
