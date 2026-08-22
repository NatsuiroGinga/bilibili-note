# 证据笔记

## 检索状态

- 项目混合索引状态：`stale=false`，构建时间 `2026-08-22T07:51:34.873207+00:00`，共 `37,395` 个向量块。
- 首次混合查询失败原因：模型库尝试访问 Hugging Face 解析已固定模型配置，当前 DNS 不可用。
- 随后以 `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` 重试成功；向量与词法通道均运行。查询触发一次增量构建，耗时 `11.379` 秒，关键命中为表格 ResNet 实施报告、第三章恢复卡和统一资格审计。

## 已确认边界

- LSPR23 为所有输入状态、配方和容量的唯一拟合与封印年度。
- LSPR24 仅在封印后作分表描述性评价，不参与拟合、选点或修订。
- 统一信息预算为 Dijk 附录 A 的 83 个字段；原始 IP 只作实体分组侧车，不进入模型特征。
- 新数据产品必须由统一清单和统一加载器服务多个消费者，不允许每个模型重复物化。
- 生产代码不得持久化无界逐样本标签或预测；本任务只设计，不运行。

## 原始数据与字段事实

- LSPR23 ZIP：`1,925,103,715` 字节，内部唯一 CSV `ls23pr_v1.csv`，未压缩 `10,588,252,004` 字节；正式入口必须从 ZIP 流式投影字段名。
- LSPR24 Parquet：`2,775,972,952` 字节，`20,227,356` 行、`21` 个行组、`101` 列。
- 两年度字段集合均为 `101` 列，但最后九列物理顺序不同；任何按列号绑定标签或身份字段的实现均无效。
- Dijk 附录 A 的 `DIJK_FEATURES` 恰有 `83` 个字段。特殊七字段为 `SrcPort`、`DstPort`、`Protocol`、`L3/L4 Protocol`、`Int/Ext Dst IP`、`External_src`、`External_dst`；其余 `76` 列是连续或计数特征。
- 原始 IP 只生成无向实体侧车；`mTimestampStart` 只用于复现现有 Protocol A 序列顺序与切分身份，不进入模型。

## Protocol A 身份

- `select_signal.seqs_full` 先按规范无向 IP 对分组，再按 `mTimestampStart` 排序，每 `128` 条连续非重叠切块；`I[s,p]` 是原始流行号，`M[s,p]` 是有效位，`E[s]` 是序列实体，`T[s]` 是序列第一条流的开始时间。
- LSPR23 固定形状：`16,353,511` 条流、`271,815` 个序列、长度 `128`。
- 切分：对 `np.unique(E23)` 用 `np.random.RandomState(42)` 排列，前 `int(150680×0.1)` 个实体作验证实体；`T23` 的 `0.85` 分位及以后为时间尾部。训练序列为 `~(entity_mask | time_mask)`，验证序列为 `entity_mask & ~time_mask`。
- 冻结统计：实体 `150,680`、训练序列 `208,598`、验证序列 `22,444`、训练与验证序列行交集 `0`。训练有效流必须由 `I23/M23` 映射并去重，不能把全年度流或验证流纳入变换、类别权重或损失权重。

## N14 审计对本设计的影响

- 父任务移交的独立审查结论指出：当前 N14 实现把验证标签纳入正类权重、在源侧完整指标与封印前读取目标、没有预算安全且并列组完整的检测率、缺首次告警指标、检查点频率与冻结合同不符、消融命名不符，并且适配表与朱论文对位未先于实现完成。因此 `812e67f` 不可直接运行。
- 数据侧根因更早：旧 `select_signal` 先对全年度 `X23` 求均值与标准差，再把同一状态应用到 `X24` 并落盘；N14 又在该标准化矩阵上拟合分位数。它既不能作为新的训练区拟合源，也不是官方分位数配方的原始输入。
- 可复用的是 Protocol A 的 `I/M/E/T` 成员语义、字段顺序、固定切分身份和官方配方证据；不可复用的是旧 `X23/X24` 的拟合语义、全年度权重统计和模型专用缓存布局。

## 官方源码核验

- 2026-08-22 运行 `git ls-remote`，官方仓库 `yandex-research/rtdl-revisiting-models` 的 `refs/heads/main` 为 `e3ed46cac38568785289d8fa16b8cfa585bde27e`。
- 官方 GitHub 提交页确认 `e3ed46c`，仓库主页确认其为论文官方实现；`lib/data.py` 当前主分支与固定提交一致。
- `lib/data.py::build_X`：数值缺失以 `np.nanmean(self.N['train'], axis=0)` 填补，随后才调用规范化。
- `lib/data.py::normalize`：标准化使用 `StandardScaler()`；分位数使用 `QuantileTransformer(output_distribution='normal', n_quantiles=max(min(n_train//30,1000),10), subsample=1e9, random_state=seed)`。
- 分位数拟合前复制训练矩阵，计算 `stds=np.std(X_train, axis=0, keepdims=True)`，噪声尺度为 `1e-3/maximum(stds,1e-3)`，并用一次 `np.random.default_rng(seed).standard_normal(X_train.shape)` 生成行主序噪声。
- 现有 FT/N14 工具的逐字段派生种子不是官方随机流；只能作为有独立状态哈希的实现偏离，不能冒充官方臂。

## 架构裁决

- 推荐“Raw83 唯一拟合源＋共享臂级物化”：LSPR23 物化候选 A、B 两份共享 `float32` 视图；源年封印后，LSPR24 只物化胜出臂一份视图。
- 不推荐训练期全在线分位数变换：Protocol A 会在多轮随机序列采样中重复访问相同流，在线插值会重复放大 CPU 和内存带宽开销。
- 不允许每模型专用视图。视图身份只由 `year + transform_state_hash + raw_content_hash + split_hash` 决定，表格 ResNet、FT-Transformer 和后续骨干共享消费。
- 候选 B 的七特殊字段“透传”冻结为复制候选 A 的训练区标准化并裁剪后的七列，绝不是把 `0..65535` 的端口原值直接送入模型；76 列分位数从 Raw83 原值拟合。
- 标签只在运行内按 `raw_row_index` 流式连接；磁盘不保存 `y23.npy`、`y24.npy`、逐流预测或逐实体预测。

## 仍待实现后核验

- 实际 B76 环境的 NumPy、scikit-learn、PyArrow 版本与所用接口签名。
- 旧 `I/M/E/T` 的完整文件 SHA、全覆盖/无重复流映射收据与新产品逐位绑定结果。
- Raw83 全量缺失、非有限、物理范围非法和时间解析计数。
- 两个 LSPR23 共享视图及胜出 LSPR24 视图的真实内容 SHA、吞吐和峰值资源。
- 官方单次行主序噪声通过磁盘映射 `out` 生成时，与同版本内存一次性生成的逐位一致性。
