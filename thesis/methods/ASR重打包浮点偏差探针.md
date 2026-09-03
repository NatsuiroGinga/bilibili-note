# ASR-重打包浮点偏差探针

<!-- RESEARCH_ROUTE=RWKV -->

- 状态日期：2026-09-03
- 定位：**可行性探针（spike）**，回答[第四章候选-BER训练效率机制](第四章候选-BER训练效率机制.md)
  候选二「聚合稀疏梯度重打包」（ASR）的待测项 T5：ASR-重打包子变体相对现状实现的
  θ 梯度浮点偏差量级
- 证据等级：**实验支持**（真实数据、真实生产函数、真实模型架构；权重为随机初始化，
  非训练检查点——理由见下）
- 探针代码用完即弃，本文档只保留可复算的关键片段，不代表生产实现

**本文件是探针结论，不是正文，也不是生产代码变更。**

---

## 一、要回答的问题

候选二 ASR 的两个子变体中，「ASR-保形」（只跳过完全不含选中流的整微批，不重打包）
已在同文档 7.1 节实测证明与现状 `torch.equal` 逐位相等。「ASR-重打包」
（把选中的流压成新的稠密批）则不然：

```
相对偏差 = ||g_repacked - g_current||_inf / ||g_current||_inf
```

差异只来自 GEMM 分块变化引起的浮点重结合律——**这个数字决定候选二能否采用**：
若稳定低于 BF16 机器精度量级（`2^-8 ≈ 3.9e-3`），可视为数值等价；否则须标注
「改变数值语义、需重跑第三章」。

## 二、测量方法

### 2.1 两条路径共享同一批输入与同一组权重

对每一次真实抽样得到的批，在同一份模型权重上分别计算两条路径的 θ 梯度：

**现状路径**（`g_current`）：
1. 全批 `(B*T,)` 展平流一次前向（建图）得 `logits`；
2. 生产函数 `ranking.prefix_scores(logits, valid, segment_owner)` 得实体分数 `S`
   （`z1'=0`，max 聚合，每实体梯度只回到一条流）；
3. 生产函数 `ranking.bag_policy_diagnostics(...)`（`active_policy="full"`）内部
   走同一条 `prefix_scores` → `cvar_pauc_loss` 链，得 `loss`；
4. `loss.backward()`，取全部共享参数梯度展平为 `g_current`。

**ASR-重打包路径**（`g_repacked`，候选二形式化的 Pass 1 / Pass 2）：
1. Pass 1（`torch.no_grad()`）：同一批同一权重再跑一次全批前向，得 detached 的
   `S`、`source_row`（`prefix_scores` 定位的取得最大值的片段）与取得最大值的列；
2. 用 detached 的 `S` 建叶张量 `Ŝ = S.clone().requires_grad_(True)`，走生产函数
   `ranking.cvar_pauc_loss(Ŝ_pos, Ŝ_neg, budgets, xi)` 反传一次，得播种梯度
   `g_seed = ∂loss/∂Ŝ`（`z1'=0` 下 `E=20` 个标量，代价与 `pairwise` 同量级）；
3. Pass 2（建图，重打包）：按 Pass 1 定位的 `(行, 列)` 从**同一份**展平输入张量里
   取出这 `E` 条被选中的流，重新前向（`model` 对任意流子集的前向在数学上与全批
   前向对该流的输出恒等——FT-Transformer 逐流独立，见候选文档 5.5 节的源码级核验），
   得 `S' = model(selected_flows)`（`z1'=0` 下聚合是恒等映射）；
4. `torch.autograd.backward(S', grad_tensors=g_seed)`，取全部共享参数梯度展平为
   `g_repacked`。

两条路径的输入张量（`numeric`/`categorical`/`valid`/`segment_owner`/`entity_is_positive`）
与 `xi` 取值逐位相同（同一次真实抽样、同一份 detached 初始化），模型权重是同一个
`nn.Module` 实例（构造后不再更新，两条路径调用间不做任何优化步）。

### 2.2 真实数据、真实生产函数

- **数据**：本机 `runs/diagnostics/dijk-repro/cache/{X23,y23,I23,M23,E23,T23}.npy`
  ——LSPR23 源年冻结数组的真实副本（`X23.npy` 5.1 GiB）。用生产函数
  `ft_mod.source_split(arrays, config)` 得到与生产逐字一致的训练区切分
  （`entity_count=150680`、`train_sequences=208598`，与收据核验通过）。
  每次试验从训练区随机抽 20 个真实实体，按 `(entity, T23)` 排序、每实体截断到
  至多 6 段——与生产 `_cap_segments_per_entity_rows` 同一原理，只是熵源不同。
- **模型**：`ft_mod.build_model(config, projection, input_key=candidate_key)`
  ——真实 `FTTransformerFieldToken` 架构（`d_token=192`、`n_layers=3`、`n_heads=8`），
  真实参数量三方核验通过（`924283`，与冻结配置记载的架构闭式和实测三方一致）。
- **排序损失路径**：`ranking.prefix_scores` / `ranking.bag_policy_diagnostics` /
  `ranking.cvar_pauc_loss` 全部是 `tools/ch3_ft_entity_ranking_loss.py` 的生产函数，
  直接 `import` 调用，不复刻。
- **输入变换**：`FieldTokenTransform`（生产类）用生产的分位数/词表拟合函数
  （`_gather_training_column` / `_fit_quantile_column` / `_fit_vocabulary`）在
  `X23` 前 500,000 行（真实数据的一个连续子集）上拟合，不是生产的全训练区拟合，
  也不做生产的掩码哈希核验——这只影响特征分布的精确度，不影响本探针要测的量
  （GEMM 分块变化引起的浮点重结合误差是模型架构与批形状的函数，与特征值的具体
  分布无关，见下节判定依据）。

### 2.3 已知简化，如实记录

1. **权重随机初始化，非训练检查点**。两条路径共享同一份权重，浮点偏差的产生机制
   （矩阵乘法分块顺序随批形状变化）与权重是否训练无关；本机无可用的第三章训练
   检查点（服务器侧产物，按仓库规则本轮不连服务器）。
2. **输入变换近似拟合**（2.2 节已述），不改变本探针的可回答性。
3. **`model.eval()`**：关闭 `attention_dropout=0.2`／`ffn_dropout=0.1`，避免 RNG
   噪声污染浮点位级比较——与同文档 7.4 节 V1 测试同一手法。
4. **只测 `z1'=0`（max 聚合）**，未覆盖 `z1'=1`（尾部聚合，`α=0.5`）。候选文档
   点名 `z1'=0` 是「唯一可能达到参照论文第四章量级」的情形（`Σ_e k_e = E`，
   `8000` 倍压缩），是本待测项的主要动机；`z1'=1` 的重打包结构相同（选中流→
   重打包前向→加权重建→播种反传），预期偏差量级同源，但未实测，**标为待验证**。
5. **`active_policy="full"`**（不做因果前缀截断）。截断策略与重打包正交
   （截断只改变 `valid` 掩码，不改变「选中流重打包后前向是否逐位等价」这一问题），
   本探针只测最简配置。

### 2.4 环境

`/opt/miniconda3/envs/rwkv/bin/python`（torch `2.12.0`，CPU；未用 MPS——`scatter_reduce`
按仓库已知限制须在 CPU，`prefix_scores` 全程走 CPU 一致更简单）。BF16 用
`torch.autocast(device_type="cpu", dtype=torch.bfloat16)` 包裹前向，模型参数保持
fp32（与生产 `cuda-bf16-amp-fp32-sensitive-v1` 精度合同的「计算 bf16、参数 fp32、
损失侧 fp32 岛」结构一致），损失与反传在 fp32 下进行。

---

## 三、结果

<!-- 占位：分阶段填入，见变更登记 -->

---

## 四、判定

<!-- 占位 -->

---

## 五、变更登记

| 时间 | 事项 | 提交 |
| --- | --- | --- |
| 2026-09-03 | 建立方法论章节；结果待填 | 本次提交 |
