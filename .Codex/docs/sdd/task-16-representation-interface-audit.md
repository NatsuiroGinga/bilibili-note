# 任务十六物理表征接口审计

## 审计结论

**接口门禁通过，可以进入最小 B0/B1 实现。** 现有 Qwen、GeNIS 和 ns-3 管线存在一条不依赖推理期队列真值的可微通路：

```text
GeNIS 提示
  -> Qwen 最终隐藏状态
  -> 最后一个提示令牌表示
  -> 五维预测队列状态 q_hat
  -> 可靠性门控物理投影
  -> 完成文本对应的最终隐藏状态
  -> Qwen 词表输出层
  -> 生成损失或自回归输出
```

推理时只需要原有 GeNIS 八个流量特征、分词器、Qwen、状态头和耦合模块，不读取 ns-3 文件、队列锚点、通量真值或物理残差。ns-3 真值只在训练和验证时监督状态头与有限队列残差。

该结论只证明**工程路径与自动微分路径可建立**，不证明 GeNIS 聚合流特征足以辨识真实队列状态。GeNIS 缺少链路容量、四窗口边界和队列通量，因此其 `q_hat` 是从跨域隐藏表征外推的物理状态估计；B0/B1 探针必须把这一点作为待验证风险，而不是已确认物理语义。

## GeNIS 输入审计

### 原始适配与可观测字段

`src/flow_probe/adapters/genis.py` 把 GeNIS Argus 流字段统一为八个不含标签的数值特征：

- `total_packets`
- `total_bytes`
- `packet_length_mean`
- `packet_length_min`
- `packet_length_max`
- `iat_mean_ms`
- `packet_rate`
- `byte_rate`

训练包 `runs/data-bundled/genis-hierarchical-v2-multitask-seed42/train.jsonl` 每条记录包含 `prompt`、`completion`、八维 `features`、任务和标签元数据。模型输入只使用 `prompt`；监督完成文本来自 `completion`。

### 提示模板

`src/flow_probe/serialize.py` 按固定字段顺序生成：

```text
任务：<攻击大类或子类判断>
流量：total_packets=...;...;byte_rate=...
只输出 JSON，label 必须为以下之一：...
```

`src/flow_probe/physics_train.py::_generation_batch` 再套用 Qwen 聊天模板，并把提示令牌的标签全部设为 `-100`。实现显式耦合时必须从第一个非 `-100` 标签的前一位置取得提示末令牌隐藏状态，禁止从包含监督完成文本的最后一个令牌预测 `q_hat`，否则会引入目标泄漏。

## ns-3 输入与监督审计

正式制品为 `runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/`。`field_roles_snapshot.json` 固定了四类字段角色。

### 允许进入状态估计器的五个字段

- `capacity_start_bps`
- `capacity_end_bps`
- `configured_capacity_integral_link_bytes`
- `qdisc_received_l3_bytes`
- `qdisc_received_packets`

每个字段包含四个窗口值。`src/flow_probe/physics_train.py::build_physics_prompt` 只序列化这五个可观测字段，不包含队列锚点、离开量、丢弃量或保存的审计残差。

### 只在训练或验证使用的真值

- 五个边界锚点来自 `queue_boundary_anchors_l3_bytes`，除以四窗口容量积分最大值后形成状态目标。
- `qdisc_dequeued_l3_bytes`、`qdisc_dropped_before_enqueue_l3_bytes` 和 `qdisc_dropped_after_dequeue_l3_bytes` 只用于现场计算有限队列残差。
- 保存的 `queue_balance_residual_*` 属于审计字段，现有数据接口会主动拒绝其进入训练。

因此，ns-3 管线已经满足“输入可观测量与监督真值分离”；新耦合模块不需要改变支柱 A 的双锚点状态监督或残差定义。

## 模型前向与隐藏状态审计

### 已有接口

- `ContinuousQueueStateHead` 是 `Linear(hidden_size, 5) + Softplus`，输入为任意 `[批量, hidden_size]` 隐藏表示，输出五个非负归一化状态。
- `select_last_token_hidden` 接受 `[批量, 序列, 维度]` 隐藏状态和二维注意力掩码，按样本提取最后一个有效令牌。
- 现有状态路径调用 `output_hidden_states=True`，从 `outputs.hidden_states[-1]` 取得最终隐藏状态。
- 现有生成路径直接调用 `model(**batch).loss`，没有调用状态头。因此当前 `dL_gen/dq_hat` 不存在，而不是数值过小。

### 服务端 Qwen3-1.7B 核验

服务端固定模型 `/root/autodl-tmp/thesis/models/Qwen3-1.7B/config.json` 与当前 `transformers` 映射核验结果为：

- 配置类：`Qwen3Config`
- 模型类：`Qwen3ForCausalLM`
- `hidden_size=2048`
- `vocab_size=151936`
- `tie_word_embeddings=true`
- `get_output_embeddings()` 可用
- 解码器 `Qwen3Model.forward` 返回 `BaseModelOutputWithPast`
- 因果语言模型 `Qwen3ForCausalLM.forward` 返回 `CausalLMOutputWithPast`

因此可以直接执行带 LoRA 的 Qwen 解码器，取得最终隐藏状态，在词表输出层之前完成融合，再由原模型的输出嵌入层计算 logits。该路径不需要修改 Qwen 残差拓扑，也不需要改写 G0 至 G5 的历史入口。

## B0/B1 最小接口

### 共同结构

1. 用最后一个提示令牌隐藏状态预测 `q_hat`，其形状为 `[批量, 5]`。
2. 用只读取 `q_hat` 的标量 Sigmoid 门产生普通可靠性权重。该门不读取真值，因而训练和推理接口一致。
3. 把 `q_hat` 投影到 2048 维，并只注入负责预测监督完成文本的隐藏位置。
4. 通过 Qwen 原词表输出层计算 logits 和标准移位因果交叉熵。
5. 自回归推理时从原始提示计算一次 `q_hat`，后续每个解码步复用它；不访问 ns-3 或队列标签。

### 唯一变体差异

- `B0`：使用普通可训练物理投影矩阵。
- `B1`：使用与 B0 完全相同的状态头、可靠性门、注入位置、初始化、损失、优化器和数据顺序；仅通过薄 QR 参数化令物理投影矩阵列满足 Stiefel 约束 `W^T W = I_5`。

首轮不加入 mHC、Birkhoff、多流残差、域对抗、博弈协调、额外权重扫描或 202 步训练。

## 必须通过的行为门禁

- 自动微分：生成损失对 `q_hat` 的梯度范数严格大于零且有限。
- 扰动：保持语言隐藏状态不变，只扰动 `q_hat`，监督输出位置的 logits 必须发生有限且非零变化。
- 无真值推理：仅给 GeNIS 提示即可计算 `q_hat`、可靠性门和下一令牌 logits。
- 因果边界：训练期 `q_hat` 只能读取提示令牌，不读取完成文本隐藏状态。
- B1 正交性：有效投影矩阵的 `||W^T W-I||_F` 在数值容差内；B0 不施加该约束。
- 变体隔离：B0/B1 之外的名称必须拒绝；历史 `physics_train.py` 与 `game_train.py` 不修改。

## 风险与停止条件

1. GeNIS 与 ns-3 的观测语义不同。前者是单流聚合统计，后者是四窗口瓶颈链路观测；状态头跨域迁移的语义有效性只能由后续实验诊断，不能由接口审计证明。
2. 最终隐藏层注入只改变词表投影前的表征，不等于改造完整 Transformer 残差拓扑。本轮只裁决这一最小显式连接是否值得扩大。
3. 若真实 Qwen 上自动微分或扰动任一门禁为零、非有限或接口报错，则停止训练，不启动 50 步实验。
4. 若任一 B0/B1 两步在线冒烟失败，则两者均不进入 50 步对照，先记录失败原因并复核接口。
