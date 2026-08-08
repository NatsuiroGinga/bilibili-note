# 受限交叉注意力第二结构支柱实现可行性审计

## 1. 审计结论

**状态：可实现，可以进入独立实施计划，但尚未获得实验有效性结论。**

推荐的唯一实现骨架是：冻结现有 S3 检测适配器与 4 位 Qwen3-1.7B 主体，从同一次解码器前向的受保护中间层提取提示末端表示，预测五个非负队列锚点；把五个锚点编码为五个条件键值，在后续解码层之前通过交叉注意力形成修正量，再由零初始化标量门和相对范数上界写入生成隐藏表示。

该骨架不需要先完成一次 Qwen 前向再进行第二次生成，也不依赖公开数据推理时不可得的队列真值。它通过挂接实际 Qwen 解码层，统一覆盖训练期因果语言模型前向、带键值缓存的 `model.generate` 和候选完成整序列评分。

**最大工程阻塞风险**是训练期梯度检查点重计算与 `generate` 多步键值缓存共享可变条件上下文。实施时必须关闭新运行的梯度检查点，并由两步真实模型冒烟证明提示预填充只执行一次、后续解码复用同一五锚点条件。未通过这一门槛不得运行 50 步。

## 2. 为什么不是任务十六原方法的重复

| 比较维度 | 任务十六 B0                                 | 本报告骨架                                           |
| -------- | ------------------------------------------- | ---------------------------------------------------- |
| 状态来源 | 完整解码器最终隐藏层的提示锚点              | 冻结中间源层的提示锚点                               |
| 写入位置 | 词表投影之前直接相加                        | 后续解码层之前写入，后续自注意力与前馈网络继续消费   |
| 条件表示 | 五维状态投影为一个共享向量                  | 五个锚点分别成为五个条件键值，查询依赖当前生成令牌   |
| 门控初值 | 零权重经 `sigmoid` 后为 `0.5`，不是恒等函数 | 标量门参数为零且经 `tanh`，新增残差严格为零          |
| 幅值保护 | 没有相对隐藏表示的显式上界                  | 每个令牌的残差二范数不超过原隐藏表示的固定比例       |
| 基座更新 | LoRA、状态头和投影共同训练                  | S3、Qwen 与全部 LoRA 冻结，只训练状态头和新增结构    |
| 生成接口 | 手写下一令牌函数，未接入正式 `generate`     | 挂接实际解码层，预填充与缓存解码均启用同一结构       |
| 候选评分 | 未接入正式候选评分                          | 显式传入提示边界，候选完成不能反向污染条件状态       |
| 关闭结构 | 没有训练后全任务严格恢复契约                | 显式旁路后在家族、子类和三个未知攻击分区恢复 S3 路径 |

因此，这不是给 B0 改名称、秩、权重或门值。它改变了计算位置、注意力计算图、首步梯度路径、检测保护方式和正式推理接口，满足失败方向重新进入的四项门槛。

## 3. 同一次 Qwen 前向中的状态预测与后续注入

### 3.1 层位置

令 Qwen 解码层数为 `L`，不扫描层位置，固定采用以下相邻中层规则：

\[
s=\left\lfloor\frac{L}{2}\right\rfloor-1,\qquad
t=\left\lfloor\frac{L}{2}\right\rfloor,
\]

其中 `s` 是状态源层，`t` 是注入发生前的目标层。加载模型后必须把 `L`、`s` 和 `t` 的实际值写入配置快照及结构清单，并验证 `0\leq s<t<L`。

选择相邻中层的原因是避免额外层位置搜索，同时让状态头读取已经形成上下文语义、但仍有后续解码层处理物理修正的表示。整个 Qwen 主体和 S3 检测适配器均冻结，因此源层表示是受保护表示。

### 3.2 三种提示锚点

| 路径                | 状态锚点位置                     | 注入位置                                                 |
| ------------------- | -------------------------------- | -------------------------------------------------------- |
| 因果语言模型训练    | 首个监督完成令牌之前的提示末令牌 | 所有预测监督完成令牌的隐藏位置                           |
| 自由生成预填充      | 每条左填充提示的最后有效令牌     | 预填充时只注入最后有效提示令牌；缓存解码时注入当前令牌   |
| 候选完成评分        | `completion_start - 1`           | 从 `completion_start - 1` 到最后一个被评分令牌的前一位置 |
| ns-3 状态与物理批次 | 每条提示的最后有效令牌           | 显式旁路，只捕获状态，不执行生成修正                     |

候选评分必须显式传入每条序列的 `completion_start`。不能用整条候选序列的最后有效令牌预测状态，否则候选标签文本会进入条件状态，破坏条件似然可比性。

### 3.3 单次前向与缓存生成

运行时在实际 `Qwen3Model.layers[s]` 上注册输出挂钩，在 `layers[t]` 上注册带关键字参数的前向预挂钩，不拆写 Qwen 的因果掩码、旋转位置编码或键值缓存实现。

一次普通前向按以下顺序执行：

1. Qwen 执行至源层 `s`，源层挂钩从提示锚点取得隐藏表示并预测五锚点状态。
2. 原模型继续执行至目标层 `t`，目标层预挂钩用已预测状态计算受限交叉注意力并改写目标层输入。
3. 原模型继续执行余下层和词表投影，返回标准因果语言模型输出。

自由生成由运行时的 `generate` 方法建立一次生成会话后委托给原 `PeftModel.generate`。第一次预填充在源层计算并缓存 `q_hat`；以后每个单令牌缓存解码步只复用该条件，不重新估计、不执行第二次提示前向。评估协议固定为贪心生成和单束搜索；若 `num_beams != 1`，运行时必须拒绝执行，因为束扩展和重排尚未纳入本次有界合同。

## 4. 精确计算图与张量形状

### 4.1 五锚点状态

设批量为 `B`、序列长度为 `T`、Qwen 隐藏维度为 `d`、状态锚点数固定为 `K=5`、交叉注意力瓶颈维度为 `r`、注意力头数为 `H`，且 `r` 能被 `H` 整除。

源层输出为

\[
H^{(s)}\in\mathbb{R}^{B\times T\times d}.
\]

由每条样本的提示锚点 `a_i` 取得

\[
h_i^{(s)}=H^{(s)}_{i,a_i,:}\in\mathbb{R}^{d},
\qquad
\hat{q}_i=\operatorname{Softplus}(W_qh_i^{(s)}+b_q)
\in\mathbb{R}_{\geq 0}^{5}.
\]

`W_q` 与 `b_q` 复用 `ContinuousQueueStateHead` 的参数语义，但状态输入改为已冻结的中间源层表示。状态损失和有限队列残差仍直接作用于 `q_hat`，不修改双锚点监督或 `queue_balance_residual`。

### 4.2 五个条件键值

第 `j` 个锚点使用独立的可学习锚点标识 `e_j`，状态值先执行 `log1p` 压缩：

\[
c_{i,j}=\operatorname{MLP}_{c}
\left([\log(1+\hat q_{i,j});e_j]\right),
\qquad
C\in\mathbb{R}^{B\times 5\times r}.
\]

目标层输入记为 `H^(t) in R^(B x T x d)`。瓶颈交叉注意力为

\[
Q=\operatorname{RMSNorm}(H^{(t)})W_Q
\in\mathbb{R}^{B\times H\times T\times r/H},
\]

\[
K=CW_K,\qquad V=CW_V
\in\mathbb{R}^{B\times H\times 5\times r/H},
\]

\[
A=\operatorname{softmax}
\left(\frac{QK^\top}{\sqrt{r/H}}\right)
\in\mathbb{R}^{B\times H\times T\times 5},
\]

\[
Z=\operatorname{Concat}(AV)W_O
\in\mathbb{R}^{B\times T\times d}.
\]

这使不同生成位置能够按查询内容选择五个锚点，而不是把一个固定投影向量无差别加到全部位置。

### 4.3 零初始化恒等旁路与幅值界

设 `m_(i,u)` 是注入掩码，固定残差比例上限为 `eta > 0`，数值稳定常数为 `epsilon > 0`，唯一零初始化参数为标量 `alpha=0`。对第 `i` 条样本、第 `u` 个令牌定义

\[
\Delta h_{i,u}
=m_{i,u}\,\eta\tanh(\alpha)\,
\operatorname{stopgrad}(\lVert h^{(t)}_{i,u}\rVert_2)
\frac{z_{i,u}}{\lVert z_{i,u}\rVert_2+\epsilon},
\]

\[
\widetilde h^{(t)}_{i,u}=h^{(t)}_{i,u}+\Delta h_{i,u}.
\]

当 `alpha=0` 时，`tanh(alpha)=0`，所以对任意输入和任意交叉注意力参数都有

\[
\widetilde H^{(t)}=H^{(t)}.
\]

因此新增结构在初始化时与 S3 检测路径函数等价，而不是近似等价。由于

\[
\frac{\lVert z\rVert_2}{\lVert z\rVert_2+\epsilon}<1,
\qquad |\tanh(\alpha)|<1,
\]

可得逐令牌相对残差界

\[
\lVert\Delta h_{i,u}\rVert_2
<m_{i,u}\,\eta\lVert h^{(t)}_{i,u}\rVert_2.
\]

`eta` 是预注册的结构常数，不在本次方向实验中扫描。实现必须先检查 `Z` 和状态均为有限数，再计算乘法，避免 `0 * NaN` 破坏恒等性质。

## 5. 首步梯度与物理信息路径

令冻结的 Qwen 与 S3 参数为 `phi`，状态头参数为 `theta_q`，条件编码和交叉注意力参数为 `theta_c`，零门参数为 `alpha`。

初始化 `alpha=0` 时，生成损失的梯度满足：

\[
\nabla_{\theta_c}\mathcal{L}_{gen}=0,\qquad
\nabla_{\hat q}\mathcal{L}_{gen}=0,\qquad
\nabla_{\theta_q}^{gen}\mathcal{L}_{gen}=0.
\]

门参数的梯度一般不为零：

\[
\left.\frac{\partial\mathcal{L}_{gen}}{\partial\alpha}\right|_{\alpha=0}
=\eta\sum_{i,u}m_{i,u}
\left\langle
\nabla_{h_{i,u}}\mathcal{L}_{gen},
\operatorname{stopgrad}(\lVert h_{i,u}\rVert_2)
\frac{z_{i,u}}{\lVert z_{i,u}\rVert_2+\epsilon}
\right\rangle.
\]

因此第一步只由生成损失打开门。组合组中的状态头同时从双锚点状态损失和有限队列物理损失获得梯度。第一次优化后，只要 `alpha` 离开零点，第二步生成损失即可沿

\[
\mathcal{L}_{gen}
\rightarrow \widetilde H^{(t)}
\rightarrow Z
\rightarrow C(\hat q)
\rightarrow \hat q
\rightarrow \theta_q
\]

到达状态头，并同时更新 `theta_c`。

物理损失只更新状态头，不直接更新交叉注意力，也不更新冻结的检测模型：

\[
\nabla_{\theta_q}(\mathcal{L}_{state}+0.01\mathcal{L}_{physics})\neq 0,
\qquad
\nabla_{\theta_c}\mathcal{L}_{physics}=0,
\qquad
\nabla_{\phi}\mathcal{L}_{physics}=0.
\]

这是针对 D2/D3 失败证据的主动隔离：物理梯度负责塑造五锚点状态，生成梯度负责学习如何有限地消费该状态，物理梯度不再直接移动检测适配器或 Qwen 表征。记录时必须分别保存 `physics_to_state_head_gradient_norm`、`physics_to_injector_gradient_norm` 和 `generation_to_state_gradient_norm`；第二项应按设计为零，不能把它误报为梯度链失败。

## 6. PEFT、4 位模型与三条调用路径

### 6.1 最小侵入集成

- 仍用 `AutoModelForCausalLM` 加载 4 位 NF4 Qwen3-1.7B，再用 `PeftModel.from_pretrained` 加载现有 S3 检测适配器。
- 不增加第二个 LoRA，不修改 PEFT 模块名，不替换 Qwen 解码层对象，避免破坏适配器保存键。
- 显式冻结 Qwen 与 S3 的全部参数，并保持 S3 检测适配器始终激活；禁止按家族、子类或未知攻击标签切换结构。
- 状态头和交叉注意力作为外部运行时的注册子模块，以 `bfloat16` 计算，必要的范数和损失转为 `float32`。
- 新训练加载阶段调用 `prepare_model_for_kbit_training(..., use_gradient_checkpointing=False)`，并验证 `model.is_gradient_checkpointing` 为假。否则挂钩上下文可能在反向重计算时已经清除。
- 运行时只在单进程、单 GPU、非嵌套会话中使用；发现嵌套前向或未清理的生成上下文时立即失败。

### 6.2 训练期因果语言模型前向

`PhysicsConditionedRuntime.forward` 接收 `input_ids`、`attention_mask` 和 `labels`。运行时由标签计算提示锚点与监督预测掩码，把其余参数原样交给 `PeftModel.forward`。返回值保留标准 `loss`、`logits` 和缓存字段，并附加 `predicted_state`、门值、注意力熵、残差比例和挂钩调用计数。

### 6.3 自由生成

`PhysicsConditionedRuntime.generate` 从 `attention_mask` 计算提示末端锚点，建立生成会话，然后委托给原 `PeftModel.generate`。源层挂钩仅在预填充时生成一次状态；目标层挂钩在预填充的最后有效令牌和以后每个缓存解码令牌生效。`finally` 块必须无条件清理状态缓存和挂钩会话。

### 6.4 候选完成评分

新评估器保留原 `CandidateSequence.completion_start`，为每个候选序列传入明确的提示锚点和评分预测掩码。相同流量提示的不同候选必须得到相同 `q_hat`；保存 `candidate_condition_repeat_max_diff`，超过预注册数值容差即判评估失败。

## 7. 显式旁路与训练后检测保护审计

运行时提供不可学习的 `bypass=True` 开关。旁路同时停用源层状态捕获和目标层注入，直接执行原 S3/PeftModel 路径。

保护审计分两层执行：

| 时点   | 审计内容                                      | 通过条件                                                                       |
| ------ | --------------------------------------------- | ------------------------------------------------------------------------------ |
| 初始化 | 同一批输入比较结构启用且 `alpha=0` 与显式旁路 | 数学上恒等；真实模型 logits 最大绝对差不超过预注册浮点容差                     |
| 训练后 | 比较显式旁路与训练前 S3                       | Qwen 与 S3 参数摘要完全一致；六个分区的固定样本 logits、自由生成和候选决策一致 |

训练前后必须保存 Qwen 冻结参数摘要、S3 适配器摘要和意外可训练参数清单。任何 Qwen 或 S3 参数变化都使运行无效。

训练后旁路审计不能只检查家族任务。两步冒烟至少从 `family_test`、`subtype_validation`、`subtype_test`、`ood_dos_icmp`、`ood_dos_pushack` 和 `ood_dos_udp` 各取一个固定样本，同时检查训练前向、贪心生成和全部候选评分。正式 `eval300` 还应保存旁路预测文件并与 S3 的 12 个既有预测文件逐样本核对。

## 8. 四组消融的统一合同

四组均加载同一冻结 S3，实例化同形状状态头和交叉注意力，使用相同数据、样本顺序、批量、步数和前向调度。关闭的损失仍执行无梯度前向以记录同预算成本，不用真值作为推理输入。

| 组别        | 生成损失 | 双锚点状态与物理损失 | 注入 | 条件向量语义                                       | 作用                               |
| ----------- | -------- | -------------------- | ---- | -------------------------------------------------- | ---------------------------------- |
| 基础模型    | 不更新   | 不更新               | 旁路 | 不使用                                             | 复用冻结 S3 检测输出               |
| PINN 单支柱 | 不更新   | 开启                 | 旁路 | 受 PINN 监督的五锚点状态                           | 证明状态和守恒机制，不改变检测路径 |
| 结构单支柱  | 开启     | 关闭                 | 开启 | 同一状态头产生的五维非负条件潜变量，不宣称物理含义 | 隔离结构容量与零门保护作用         |
| 组合方法    | 开启     | 开启                 | 开启 | 受 PINN 监督的五锚点状态                           | 检验物理状态是否转化为检测收益     |

“结构单支柱从何得到条件状态”的答案是：从与组合组完全相同的冻结源层和同形状状态头得到，但不施加状态真值或物理残差监督。它只是五维条件潜变量，不能在论文中称为队列状态。这样保持参数量、计算图和推理接口一致，并把组合组相对结构单支柱的差异限定为 PINN 监督。

基础模型可以直接复用 S3 正式检测制品；PINN 单支柱、结构单支柱和组合方法需要独立运行。四组不引入新的学习率、损失权重或秩扫描。

## 9. 精确文件和接口范围

以下名称是工程职责名，不是最终论文算法名。

### 9.1 新增文件

| 文件                                                       | 必须提供的接口                                                                                                                                                                           |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/flow_probe/bounded_physics_conditioning.py`           | `BoundedPhysicsCrossAttention`、`ConditioningDiagnostics`、`PhysicsConditionedRuntime`、`resolve_conditioning_layers`、`build_training_injection_mask`、`build_candidate_injection_mask` |
| `src/flow_probe/bounded_physics_train.py`                  | `ConditioningVariantContract`、`ConditioningTrainingSettings`、`train_bounded_physics_conditioning`、四组不可变损失开关、梯度与旁路审计                                                  |
| `src/flow_probe/bounded_physics_evaluation.py`             | 结构加载、六分区自由生成、候选评分、旁路对照和效率记录；复用原评估纯函数                                                                                                                 |
| `configs/bounded_physics_conditioning_seed42.yaml`         | 固定训练数据、物理数据、批量、种子、状态与物理权重及结构参数                                                                                                                             |
| `configs/bounded_physics_conditioning_seed42_eval300.yaml` | 固定六分区、每类 300 条、生成与评分批量及 S3 比较路径                                                                                                                                    |
| `scripts/run_bounded_physics_conditioning.sh`              | `pinn_only`、`structure_only`、`combined` 和唯一输出目录                                                                                                                                 |
| `scripts/run_bounded_physics_conditioning_eval.sh`         | 加载指定训练目录执行正式评估，不复用 D1/D2/D3 硬编码路径                                                                                                                                 |
| `scripts/run_bounded_physics_conditioning_analysis.sh`     | 调用既有 2,000 次配对统计，保持九项门槛不变                                                                                                                                              |
| `tests/test_bounded_physics_conditioning.py`               | 形状、恒等、幅值界、首步和次步梯度、锚点与缓存会话                                                                                                                                       |
| `tests/test_bounded_physics_train.py`                      | 四组开关、冻结参数、保存加载和制品契约                                                                                                                                                   |
| `tests/test_bounded_physics_evaluation.py`                 | 训练前向、自由生成、候选评分均启用结构，旁路恢复和候选条件无泄漏                                                                                                                         |

### 9.2 修改文件

- `pyproject.toml`：只新增训练和评估控制台入口。
- 不修改 `asymmetric_physics_train.py`、`representation_coupling.py`、D1/D2/D3 配置或包装器、现有九项门槛和正式运行目录。

### 9.3 配置字段

结构配置至少固定以下字段：

```yaml
conditioning:
  state_size: 5
  source_layer_rule: middle_previous
  target_layer_rule: middle
  attention_bottleneck_size: <实施计划冻结的唯一值>
  attention_heads: <实施计划冻结的唯一值>
  residual_ratio_cap: <实施计划冻结的唯一值>
  norm_epsilon: <实施计划冻结的唯一值>
  gate_init: 0.0
  freeze_base_model: true
  freeze_detection_adapter: true
  gradient_checkpointing: false
  generation_num_beams: 1
```

占位值必须由后续 `writing-plans` 根据模型隐藏维度和一次显存预检固定为唯一值，不能在运行脚本中形成列表或扫描。论文算法名称也不能使用上述工程占位名。

## 10. 保存与加载契约

每个完成的训练目录新增以下制品：

1. `structure_config.json`：结构模式、模型隐藏维度、层数、解析后的源层与目标层、瓶颈、头数、残差上限、数值常数和模式开关。
2. `structure_state.pt`：只包含状态头、条件编码器、交叉注意力和门参数的 CPU 状态字典。
3. `base_binding.json`：S3 适配器绝对来源、目录摘要、基座标识和配置摘要，不保存凭据。
4. `gradient_path.json`：首步与次步的生成到门、生成到状态、物理到状态、物理到注入器梯度范数。
5. `runtime_path_audit.json`：三条路径的挂钩次数、提示预填充次数、缓存步数、结构启用差和旁路差。
6. `bypass_equivalence.json`：初始化和训练后六分区固定样本的对照结果。

加载时先建立 4 位 Qwen 和 S3，再核对 `base_binding.json`，根据 `structure_config.json` 创建同形状模块，最后使用 `torch.load(..., weights_only=True)` 和 `load_state_dict(..., strict=True)`。出现缺键、多键、层数不符、隐藏维度不符、S3 摘要不符或门值非有限时立即拒绝评估。

公开数据推理只接收 `input_ids`、`attention_mask`、提示边界和结构权重。接口必须拒绝 `state_targets`、队列真值、ns-3 场景号、攻击真值标签或未知攻击标记进入运行时。

## 11. 最小服务器目标测试与两步冒烟

### 11.1 目标测试

只在 GPU 服务器项目 `uv` 环境运行：

```bash
uv run --no-sync pytest -q \
  tests/test_bounded_physics_conditioning.py \
  tests/test_bounded_physics_train.py \
  tests/test_bounded_physics_evaluation.py
```

目标测试必须覆盖：

- 形状、非负状态、五个键值和无效配置拒绝。
- `alpha=0` 的函数恒等和逐令牌相对残差界。
- 第一步只有门获得生成梯度；组合组状态头获得物理梯度。
- 第一次更新后，第二步生成损失到状态、条件编码器和交叉注意力的梯度非零。
- 状态置零、跨样本置换和固定扰动能改变结构启用时的监督位置 logits。
- 结构旁路在训练前后恢复冻结模型输出。
- 训练前向、自由生成和候选评分三条路径的源层与目标层挂钩均被调用。
- 自由生成只有一次全提示预填充，后续调用均为缓存单令牌。
- 同一提示的全部候选完成得到相同条件状态。
- 保存加载往返后结构输出、门值和旁路输出一致。

### 11.2 两步真实模型冒烟门槛

两步冒烟使用 Qwen3-1.7B、4 位 NF4、冻结 S3、真实 GeNIS 与 ns-3 小批量，并同时执行以下门槛：

1. 初始化时结构启用与旁路的 logits 差不超过预注册浮点容差，Qwen 与 S3 摘要一致。
2. 第一步门梯度有限且非零；生成到状态和注入器梯度为零；组合组物理到状态梯度有限且非零。
3. 第一次更新后门参数离开零点；第二步生成到状态及注入器聚合梯度有限且非零。
4. 第二步状态置零、跨样本置换和固定扰动至少各使一个监督位置 logits 产生超过数值噪声的变化。
5. `model.generate` 的结构启用与旁路得分张量不同，旁路与原 S3 一致；不要求两步后贪心标签一定改变。
6. 候选评分的结构启用与旁路 logits 不同，同一提示各候选的状态重复差不超过容差。
7. 六个评估分区各一条样本的训练后旁路结果与原 S3 一致，不能只验证家族任务。
8. 运行时记录一次全提示预填充和若干单令牌缓存步，禁止出现第二次全提示前向。
9. 峰值显存、两步总时长、三条路径吞吐和延迟均成功写入本地日志与 SwanLab；冒烟阶段只记录，不设置虚构的效率提升门槛。

任何一项失败都先停止，不启动 50 步。两步全通过后，才按总控中的一次性合同运行四组中的三个新增训练组，并以固定九项门槛裁决组合方法。

## 12. 开销来源与报告方式

新增参数来自状态头、五个锚点标识、条件编码器、瓶颈查询/键/值投影、输出投影和一个标量门。若瓶颈维度为 `r`，主要参数阶数为 `O(dr+r^2)`，不复制任何 Qwen 层，也不增加第二套 LoRA。

新增训练计算来自一个中间状态头、长度仅为 5 的交叉注意力和注入点之后冻结解码层的输入梯度。因为基座冻结，源层之前不需要保存基座参数梯度；但关闭梯度检查点会增加部分激活驻留，这是必须实测的主要显存来源。

自由生成不增加第二次 Qwen 前向。预填充只增加一次状态头和交叉注意力；每个缓存解码步只对五个条件键值执行一次交叉注意力。候选评分也只执行一次整序列 Qwen 前向。正式报告必须独占 GPU，分别记录参数量、峰值显存、训练时间、样本吞吐、自由生成延迟第 50 与第 95 百分位、候选评分吞吐；本审计不预设或虚构具体数值。

## 13. 停止条件

- 挂钩未覆盖三条正式路径，或 `generate` 出现第二次完整提示前向，停止。
- 初始化不能恢复恒等函数，或训练后旁路不能恢复六分区 S3 路径，停止。
- 第二步生成损失仍不能到达预测状态和交叉注意力，停止。
- 候选状态受候选完成文本影响，停止。
- 两步冒烟超过 RTX 5090 可用显存，先报告实测来源，不通过改小数据、改物理公式或临时扫描层位掩盖。
- 50 步即使状态与物理误差改善，只要检测、未知攻击或校准门槛失败，仍判该结构失败，不追加同方法的层位置、瓶颈、头数或残差上限扫描。

## 14. 本次审计边界

- 已读取第二结构支柱研究合同、恢复文档和本地实现源码。
- 未修改实验源码、配置、测试或既有制品。
- 未启动服务器测试、训练或评估。
- 未把工程职责名写成最终论文算法名。
