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

20 次试验的批规模因真实实体袋大小异质（源年验证集袋大小中位数 2，见候选文档
5.2 节）而变化：`B ∈ [20, 30]` 个片段（`B*T ∈ [2560, 3840]` 槽位），
`z1'=0` 下选中流数恒为 `E=20`（每实体一条流，与形式化「恒等映射」一致）。

### 3.1 float32

| 统计量 | 相对偏差 `‖Δg‖_∞/‖g_current‖_∞` | 绝对偏差 `‖Δg‖_∞` |
| --- | ---: | ---: |
| 最小 | `2.8254e-07` | — |
| 中位 | `4.4855e-07` | `4.7684e-07` |
| P90 | `6.9929e-07` | — |
| 最大 | `9.4997e-07` | `7.1526e-07` |

`‖g_current‖_∞`（分母，θ 梯度的无穷范数）在 20 批间落在 `[0.439, 1.688]`，
中位 `1.134`——不是接近零的病态小量，相对偏差的分母有意义（无需额外用绝对量级
兜底解读，但仍列出绝对量级供交叉核对）。

相对偏差中位 `4.49e-07`、最大 `9.50e-07`，量级与 float32 机器精度
`eps = 2^-23 ≈ 1.19e-07` 同阶（约 `2.4`–`8` ulp），与同文档 7.4 节 V1
（前向 logits 比较，float32 相对误差 `9.56e-07`）**几乎同一量级**——
两次独立测量（一次测前向输出、一次测 θ 梯度）互相印证。

### 3.2 float64

同一批次序列（20 批，与 3.1 节逐批对应，`B*T ∈ [2560, 3840]`）在权重与输入
原样 `.double()` 升精度后重跑：

| 统计量 | 相对偏差 `‖Δg‖_∞/‖g_current‖_∞` | 绝对偏差 `‖Δg‖_∞` |
| --- | ---: | ---: |
| 最小 | `4.9839e-16` | — |
| 中位 | `9.5706e-16` | `9.4369e-16` |
| P90 | `1.3948e-15` | — |
| 最大 | `1.7853e-15` | `1.5543e-15` |

`‖g_current‖_∞` 在 float64 下与 float32 下逐批数值一致（同一权重同一输入，
双精度只是升格重算，中位 `1.134`、区间 `[0.439, 1.688]`），确认两种精度测的
是同一组批次、同一现象。

相对偏差中位 `9.57e-16`、最大 `1.79e-15`，量级与 float64 机器精度
`eps = 2^-52 ≈ 2.22e-16` 同阶（约 `2.2`–`8` ulp），与同文档 7.4 节 V1
（float64 相对误差 `1.13e-15`）**同一量级**——三次独立测量（V1 前向比较、
本探针 fp32 梯度、本探针 fp64 梯度）在各自精度下都稳定落在个位数 ulp，
互相印证「误差来自 GEMM 分块变化引起的浮点重结合律」这一机制归因，
排除「两遍播种反传结构本身引入额外误差」的可能——若是后者，fp64 下的误差
不会随精度升高而线性收窄到 `eps` 量级，而是会停留在某个与精度无关的绝对值上。

### 3.3 bf16（CPU autocast，参数与损失侧 fp32）

同一批次序列，前向包在 `torch.autocast(device_type="cpu", dtype=torch.bfloat16)`
内（矩阵乘法降到 bf16 计算，模型参数仍是 fp32，损失与反传在 fp32 下进行，
与生产 `cuda-bf16-amp-fp32-sensitive-v1` 精度合同的分工一致）：

| 统计量 | 相对偏差 `‖Δg‖_∞/‖g_current‖_∞` | 绝对偏差 `‖Δg‖_∞` |
| --- | ---: | ---: |
| 最小 | `4.8225e-05` | — |
| 中位 | `1.1243e-04` | `1.2207e-04` |
| P90 | `1.7677e-04` | — |
| 最大 | `2.7293e-04` | `2.4414e-04` |

`‖g_current‖_∞` 中位 `1.102`，区间 `[0.414, 1.805]`，与 fp32/fp64 同批次序列
量级一致（bf16 下模型输出本身也因量化而与 fp32/fp64 略有不同，故 `g_current`
的具体值随精度小幅漂移，但量级不变，仍可支撑相对偏差的解读）。

**与 BF16 机器精度的对比**：`bf16` 的机器精度 `eps = 2^-8 ≈ 3.9063e-03`
（8 位有效尾数）。本探针测得的相对偏差中位 `1.124e-04`、P90 `1.768e-04`、
最大 `2.729e-04`，**比 `eps` 低约 `14`–`81` 倍**（中位低 `35` 倍，最大的单次
观测也低 `14` 倍）——20 次试验中没有一次逼近、更没有超过 `eps` 量级。

一个执行细节的记录（不改变结论）：`compute_gradients_for_batch` 里 bf16
路径把前向输出显式 `.to(torch.float32)` 后再进入损失（`_forward` 函数末尾），
这与生产 `precision.fp32_island` 在进入 `bag_policy_diagnostics` 前把
`entity_logits` 转 fp32 的做法一致，即 bf16 的量化误差只发生在模型内部的
矩阵乘法与激活，不发生在损失计算本身——这是与生产精度合同保持一致的必要处理，
不是为了压低误差而做的特殊处置。

---

## 四、判定

### 4.1 三个独立量级观测的一致性

| 精度 | 本探针 θ 梯度相对偏差（中位／最大，`n=20`） | 该精度机器精度 `eps` | 相对 `eps` 的 ulp 数（中位） | 候选文档 7.4 节 V1（前向 logits，独立测量） |
| --- | ---: | ---: | ---: | ---: |
| float32 | `4.4855e-07` / `9.4997e-07` | `1.1921e-07` | `≈3.8` ulp | `9.56e-07`（相对） |
| float64 | `9.5706e-16` / `1.7853e-15` | `2.2204e-16` | `≈4.3` ulp | `1.13e-15`（相对） |
| bf16 | `1.1243e-04` / `2.7293e-04` | `3.9063e-03` | `≈0.029` eps（远低于 1 ulp） | 未测（V1 只测了 fp64/fp32） |

float32 与 float64 两个精度下，本探针测得的 θ 梯度相对偏差都稳定落在
个位数 ulp（`3.8`–`4.3` ulp），且与候选文档 7.4 节用**完全不同的测量对象**
（前向 logits 的重打包偏差，而非 θ 梯度）、**完全不同的模型**（同构逐行模型，
非本探针的真实 `FTTransformerFieldToken`）、**完全不同的数据**（该节用合成批，
本探针用真实 LSPR23 数据）得到的结果几乎同一量级。三次相互独立的测量
（V1 前向比较、本探针 fp32 梯度、本探针 fp64 梯度）指向同一机制归因：
**误差纯粹来自 GEMM 分块变化引起的浮点重结合律，不是两遍播种反传结构本身
引入的额外误差，也不是重打包破坏了「FT-Transformer 逐流独立」这一数学性质**
（若后者成立，误差会是 `O(1)` 量级，且不会随精度提升而线性收窄到各自
`eps` 附近——这正是本探针相对候选文档 7.4 节 V1 的增量价值：V1 只测了
「模型是否逐流独立」，本探针进一步确认「重打包 + 播种反传的整条链路」
在真实生产损失路径下同样只引入浮点级偏差）。

### 4.2 判定

**可视为数值等价。**

- `float32`：相对偏差最大 `9.50e-07`，远低于 `float32` 自身 `eps ≈ 1.19e-07`
  的 `10` 倍量级（约 `8` ulp），与生产实际使用的精度相比误差可忽略。
- `float64`：相对偏差最大 `1.79e-15`，同样在个位数 ulp。
- `bf16`（生产实际使用的计算精度）：相对偏差中位 `1.12e-04`、最大 `2.73e-04`，
  **稳定低于 BF16 机器精度量级 `eps ≈ 3.91e-03` 一到两个数量级**（20/20 次试验
  无一例外），满足候选文档冻结的支持判据「稳定低于 BF16 机器精度量级」。

### 4.3 判定的适用边界（如实记录，不构成对判定本身的削弱）

- **只覆盖 `z1'=0`（max 聚合）**，`z1'=1`（尾部聚合）未实测，标为待验证——
  但重打包的选中流数从 `E` 增至 `Σ_e k_e`（`z1'=1` 下 `α=0.5` 约为全体有效流的
  一半），**打包批规模更接近全批**，理论上浮点重结合误差应更小或同量级，
  不应比本次结果更差；若要在正文中使用 `z1'=1` 的量级，仍须补测。
- **权重随机初始化，非训练检查点**。误差机制（矩阵乘法分块顺序随批形状变化）
  在数学上与权重取值无关，但严格意义上「训练后期权重下是否仍然如此」未被
  本轮直接验证，标为待验证假设（可证伪：用第三章训练检查点重跑本探针，
  预期误差量级不变——若变化超过一个数量级，则本判定的适用范围需要收窄）。
- **`FieldTokenTransform` 为近似子集拟合**，不是生产全训练区拟合（2.3 节已述）。
  这只影响特征分布的精确度，不影响「GEMM 分块变化引起的浮点重结合误差」这一
  被测量本身——该误差是模型架构与批形状的函数，此推理已被 4.1 节的三方
  独立测量交叉验证支持，不是未经检验的假设。
- **`active_policy="full"`**，未覆盖因果前缀截断分支；候选文档已论证截断与
  重打包正交（截断只改变 `valid` 掩码），本判定的适用范围包含截断分支。
- 一次运行意外事故（如实记录，不影响结论有效性）：本探针的 bf16 阶段首次
  运行时因单次后台调用累计墙钟约 `59` 分钟被环境终止在第 `8/20` 批，
  已完成的 `8` 批（trial 00-07）原样保留、其余 `12` 批（trial 08-19）用同一
  权重构造顺序（`seed=42`）续跑补齐，20 批数据完整、独立同分布采样过程未受影响。

---

## 五、关键代码片段（可复算）

探针脚本本身不入仓库（会话临时目录，跑完即删），下列片段是其核心逻辑的原样摘录，
使结论可独立复算。完整依赖是生产模块
`tools/ch3_ft_transformer_field_token_protocol_a.py`（模型构造、真实数据视图）与
`tools/ch3_ft_entity_ranking_loss.py`（排序损失）。

```python
# 现状路径：g_current
model.zero_grad(set_to_none=True)
logits_flat = model(numeric_t, categorical_t)          # 全批展平，建图
logits_bt = logits_flat.reshape(B, T)
bag_result = ranking.bag_policy_diagnostics(
    logits_bt, valid_bool, segment_owner_t, entity_is_positive_t,
    entity_chain_length, eff_budgets, xi_current, bag_config,   # active_policy="full"
)
bag_result["loss"].backward()
g_current = torch.cat([p.grad.detach().reshape(-1).to(torch.float64)
                        for p in model.parameters()])

# ASR-重打包路径：g_repacked
model.zero_grad(set_to_none=True)
with torch.no_grad():
    logits_flat_1 = model(numeric_t, categorical_t)     # Pass 1：无梯度全批前向
    logits_bt_1 = logits_flat_1.reshape(B, T)
    filled_1 = logits_bt_1.masked_fill(~valid_bool, float("-inf"))
    seg_col_idx_1 = filled_1.argmax(dim=1)
    scores_1, source_row_1 = ranking.prefix_scores(logits_bt_1, valid_bool, segment_owner_t)
    selected_col = seg_col_idx_1[source_row_1]
    flat_pos = source_row_1 * T + selected_col           # 每实体恰一条流的展平下标

S_detached = scores_1.clone().requires_grad_(True)       # 叶张量，E 个标量
loss_seed, _ = ranking.cvar_pauc_loss(
    S_detached[entity_is_positive_t], S_detached[~entity_is_positive_t],
    eff_budgets, xi_pass1,
)
loss_seed.backward()
g_seed = S_detached.grad.clone()                          # ∂loss/∂S_e，E 维播种梯度

packed_num = numeric_t[flat_pos]                          # Pass 2：只取选中的 E 条流
packed_cat = categorical_t[flat_pos] if categorical_t is not None else None
packed_logits = model(packed_num, packed_cat)              # 建图，规模从 B*T 降到 E
S_prime = packed_logits                                    # z1'=0 下聚合是恒等映射

model.zero_grad(set_to_none=True)
torch.autograd.backward(S_prime, grad_tensors=g_seed)       # 播种反传
g_repacked = torch.cat([p.grad.detach().reshape(-1).to(torch.float64)
                         for p in model.parameters()])

rel_inf = float((g_repacked - g_current).abs().max()) / float(g_current.abs().max())
```

数据与模型构造（真实生产函数，非复刻）：

```python
config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
receipt = ft_mod.load_cardinality_receipt(str(RECEIPT_PATH), config)
roles = ft_mod.resolve_field_roles(candidate_key, config)
projection = ft_mod.project_token_layout(candidate_key, receipt, config)
torch.manual_seed(42)
model = ft_mod.build_model(config, projection, input_key=candidate_key)  # 真实架构，随机初始化
model.eval()

arrays = {name: np.load(CACHE_ROOT / f"{name}.npy", mmap_mode=("r" if name == "X23" else None))
          for name in ("X23", "y23", "I23", "M23", "E23", "T23")}        # 真实 LSPR23 冻结数组
train_rows, validation_rows, stats = ft_mod.source_split(arrays, config)  # 真实训练区切分
view = ft_mod.ProtocolASourceView(arrays, transform)                     # transform：见 2.2 节的近似拟合
```

---

## 六、变更登记

| 时间 | 事项 | 提交 |
| --- | --- | --- |
| 2026-09-03 | 建立方法论章节；结果待填 | `b2f7399` |
| 2026-09-03 | 补入 float32 结果（20 批）：rel_inf 中位 `4.49e-07`、最大 `9.50e-07`，与 7.4 节 V1 float32 结果同量级 | `422d754` |
| 2026-09-03 | 补入 float64 结果（20 批，与 fp32 同批次序列）：rel_inf 中位 `9.57e-16`、最大 `1.79e-15`，随精度线性收窄到 eps 量级，支持「误差纯属浮点重结合」的归因 | `0e51772` |
| 2026-09-03 | bf16 阶段首次运行在第 8/20 批被后台墙钟上限（约 59 分钟）终止，如实记录；用同一权重构造顺序续跑补齐 12 批 | 事故记录，无独立提交（见下条） |
| 2026-09-03 | 补入 bf16 结果（20 批）：rel_inf 中位 `1.12e-04`、最大 `2.73e-04`，低于 BF16 机器精度 `eps≈3.91e-03` 一到两个数量级；给出三精度交叉验证判定「可视为数值等价」并记录判定的适用边界；补入可复算代码片段 | 本次提交 |
