# R2 物理旁路增量信号实验计划

## 目标

在不读取最终测试集、不修改样本和不削弱基线的前提下，验证 R2 物理状态与残差是否为公开流量检测提供基础字段之外的增量信息。该实验只决定 R2 是否值得进入大模型正式训练，不作为最终论文测试结果。

## 前置门禁

1. `flow_probe_r2_protocol_dataset_v0` 的公开数据字段语义、来源锁和冻结开发划分必须通过。
2. `runs/ns3-data/r2-protocol-paired-v0/` 必须完成 TCP/普通 UDP 严格配对，运行时守恒和状态真值门禁通过。
3. 只允许使用 `train-fit` 与 `calibration` 拟合物理状态估计器；公开数据最终测试、ns-3 `test` 与 `unseen-configuration` 均不可读取。
4. 若任一前置门禁为 `NO-GO`，代理只能完成代码、配置和只读输入审计，禁止生成实验结论。

## 四组对照

- `A`：冻结共享字段上的原始 HGB 基线。
- `A+P`：在完全相同共享字段和样本上加入协议适用掩码、状态估计、归一化物理残差及不确定性。
- `A+P_shuffle`：在同一数据源、传输协议和划分内部置换完整物理旁路向量，不按标签分组，破坏样本级物理对应关系但保持边际分布。
- `A+P_random`：使用仅由训练集估计的同维度、同一阶统计量随机旁路；随机数种子固定，验证集不得参与分布估计。

四组必须使用相同训练样本、开发验证样本、标签、基础字段、预处理、分类器容量、训练预算和调参次数。旁路控制不得进入基础字段，协议、数据源、文件名或配置编号不得形成标签捷径。

## 执行顺序

1. 冻结旁路模式、字段顺序、单位、缺失掩码、协议适用掩码和 SHA-256。
2. 用 ns-3 `train-fit` 拟合物理状态估计器，只用 `calibration` 冻结尺度、温度与不确定性映射。
3. 在公开数据冻结开发训练与开发验证分区生成旁路，不读取最终测试。
4. 使用种子 42、43、44 运行四组 HGB；不得按结果挑种子或批量大小。
5. 对同一样本预测执行配对自助法，报告宏平均 F1、平衡准确率、良性误报率、Brier 分数、期望校准误差、状态误差和物理残差。
6. HGB 通过后才允许把相同旁路接口迁移到 DistilBERT 或 Qwen；未通过时不得用更大模型掩盖信号缺失。

## 裁决

只有同时满足下列条件，才记为“物理旁路具有增量价值”：

1. 至少一个预冻结困难开发分区中，三种子 `A+P-A` 的宏平均 F1 均为正，且配对 95% 置信区间下界大于 0。
2. `A+P` 同时优于 `A+P_shuffle` 与 `A+P_random`，排除参数维度和边际分布解释。
3. 常规开发分区不出现超过预注册边界的检测退化。
4. 状态误差和物理残差改善方向一致；若只改善物理指标而检测无收益，只能裁决为“物理表征有效、增量检测价值未证实”。

不得设置指定 F1、看结果后重采样、改变划分、删除失败样本、挑最好种子或人为削弱 `A`。

## 文件范围

- 实现与配置：`thesis/experiments/llm_probe/` 下新建明确带 `r2_physics_sidecar` 前缀的源码、配置和包装器。
- 运行制品：`thesis/experiments/llm_probe/runs/r2-physics-sidecar-signal/`。
- 实现报告：`.Codex/docs/sdd/task-r2-physics-sidecar-signal/report.md`。

## 当前状态

`implemented / prerequisites_pending`。输入合同、四组确定性变体、开发集隔离、三种子配置、配对统计接口和正式包装器已经实现；配置仍固定为 `prerequisites_pending`，所有输入 SHA-256 保留为 `PENDING`。只有 R2 数据发布、ns-3 正式矩阵、状态估计器和旁路物化全部通过后，才能以真实摘要替换占位值并把状态改为 `ready`。在此之前包装器必须零写入停止，禁止报告实验结果。

### 已实现文件

- `src/flow_probe/r2_physics_sidecar_signal.py`
- `configs/r2_physics_sidecar_signal_seed42.yaml`
- `configs/r2_physics_sidecar_signal_seed43.yaml`
- `configs/r2_physics_sidecar_signal_seed44.yaml`
- `configs/r2_physics_sidecar_readiness_v1.example.json`
- `scripts/run_r2_physics_sidecar_signal.sh`

### 实现期裁决

1. 公开数据的隐藏物理状态不能由本实验入口猜测。入口只消费状态估计器发布的开发集旁路 Parquet 和就绪回执；回执必须证明物理拟合只读取 `train-fit` 与 `calibration`。
2. `A+P_shuffle` 在同一数据源、传输族和划分内置换完整旁路向量，不读取攻击标签；单元素层保持不变并在结果解释中保留限制。
3. `A+P_random` 对每个旁路维度从同数据源、同传输族的训练池独立抽样。训练和开发验证都只使用训练池估计边际分布；缺少对应训练层时直接失败，不跨层回退。
4. 四组直接复用 `tabular_baselines._build_model("hgb")`，保持树数、叶节点、学习率、类别权重、线程数和随机种子一致；旁路维度差异由置换与随机旁路对照排除。
5. 正式入口只接受 `train-fit` 和 `validation`。旁路制品必须精确覆盖两类开发清单，任何额外样本都会失败，防止最终测试、未知配置或开放协议样本被提前物化。
