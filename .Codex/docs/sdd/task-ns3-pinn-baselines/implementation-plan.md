# 星型 ns-3 同协议物理基线实施计划

> **执行代理要求：** 必须使用 `superpowers:subagent-driven-development` 按任务实施；实现代理可以针对本任务使用一次 `superpowers:test-driven-development`。

**目标：** 在既有星型 ns-3 四窗口冻结数据上，以完全相同的公共观测、状态监督掩码、模型容量、初始化和选择协议，运行训练集常数预测、无物理残差状态监督和标准 PINN 三类基线的种子 42、43、44。

**架构：** 新增独立的轻量物理机理基线入口，不依赖尚未冻结的 TQH-C2 A/B 或完整 `dataset-v1`，也不修改既有 Qwen、TQH-C2、GeNIS 和 ns-3 数据制品。入口复用 `physics_train.py` 的五字段契约、`anchor0_plus_one` 组级掩码、状态归一化和有限队列残差；神经基线使用同一个两层多层感知机，唯一处理变量是标准 PINN 的物理残差项。

**技术栈：** Python 3.11、PyTorch、NumPy、PyYAML、SwanLab、现有 `flow_probe.tracking` 与 `flow_probe.physics_train`。

## 全局约束

- 本轮是 `theory_selection/review_pending` 星型物理机理基线，不是完整 `dataset-v1` 的公开检测主表，不形成 R1、R2、R3 路线裁决。
- 输入固定为 `runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/`；训练、验证、测试 SHA-256 分别为 `d6a6ca23a985223401e1d650d619c2a50b255d2066769e2478cef72cc6239fa0`、`0bbbb4ea483867561c329c896cb4e7745a102cb90024c464654e0b7d673c8723`、`6e64d2ab290813a246ed8efcefd1bb19f1026c2de7b7904d111af67b4465ef94`，划分清单 SHA-256 为 `3393d76e96b9104ea78a8a52bc73e72e2298798a4a4db29dbf76ef412eb88785`。
- 模型输入只能是四窗口的 `capacity_start_bps`、`capacity_end_bps`、`configured_capacity_integral_link_bytes`、`qdisc_received_l3_bytes`、`qdisc_received_packets`；标签、场景、拓扑、路径、种子、组号和物理真值不得进入前向输入。
- 三个划分的 `sample_id` 和 `group_id` 必须两两不交叉；本轮只接受 `star-bottleneck-v1`，拒绝哑铃和停车场数据。
- 训练与归一化只读取训练集；早停和最佳权重选择只读取验证集；测试集只在最佳权重固定后加载并评价一次。
- `constant_state` 只用训练集中掩码可见的锚点计算逐锚点常数；`state_supervision` 和 `standard_pinn` 使用同一网络、初始权重、优化器、批次顺序、状态损失和验证选择指标。
- 状态监督固定为 `anchor0_plus_one`，`lambda_state=1.0`；标准 PINN 唯一额外项为现有单尺度有限队列残差的均方，固定 `lambda_physics=0.01`，不得扫描权重。
- 种子固定为 42、43、44；全部运行使用 `device=auto`，在服务器实际选择 CUDA；SwanLab 固定在线项目 `mortiswang/malicious-traffic-llm`。
- 不修改 TQH-C2、GeNIS 或 `runs/ns3-data/`；不启动候选改进 PINN；不提交、不推送、不覆盖当前脏工作树中的既有改动。

---

### 任务 1：实现统一物理基线入口

**文件：**

- 新建：`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py`
- 新建：`thesis/experiments/llm_probe/tests/test_ns3_physics_baselines.py`
- 修改：`thesis/experiments/llm_probe/pyproject.toml`

**接口：**

- `audit_star_split_inputs(...) -> AuditedStarInputs`：训练前流式校验文件哈希、样本与组隔离、文件内 `split`、星型拓扑和五字段输入合同，只保留标识而不保留测试状态与通量。
- `materialize_audited_split(...) -> PhysicsSplit` 与 `select_then_materialize_test(...)`：训练、验证先物化，测试只在选择结果冻结并通过类型校验后物化。
- `fit_train_transform(train: PhysicsSplit) -> InputTransform`：只从训练特征拟合逐维均值与标准差。
- `build_supervision_masks(split: PhysicsSplit, seed: int) -> np.ndarray`：复用现有 `anchor0_plus_one` 组级掩码。
- `fit_constant_state(train: PhysicsSplit, train_mask: np.ndarray) -> np.ndarray`：逐锚点只使用掩码可见训练真值。
- `PublicObservationStateRegressor`：展平 4×5 公共输入，经 `Linear(20,128) + SiLU + Linear(128,128) + SiLU + Linear(128,5) + Softplus` 输出五个非负归一化状态。
- `train_selected_model(...) -> SelectedModel`：只以验证集完整状态均方误差执行早停并返回最佳权重；函数签名不得接收测试集。
- `evaluate_split(...) -> SplitEvaluation`：报告完整、已观测、未观测和逐锚点状态均方误差、物理残差均方、推理时间与逐样本预测。
- `run_tracked_ns3_physics_baseline(...) -> dict[str, object]`：保存配置、环境、输入清单、泄漏审计、训练历史、最佳权重或常数状态、验证/测试预测、摘要、成本、SwanLab 指标与制品清单。

- [x] **步骤 1：先写失败测试。** 已覆盖哈希与组泄漏拒绝、非星型拒绝、五字段严格输入、常数只使用训练可见锚点、训练函数不接受测试集、两种神经基线同种子初始权重相同、标准 PINN 唯一增加物理损失、残差对预测状态可微、验证集选择和完整制品布局。
- [x] **步骤 2：在服务器运行精确测试并确认失败。** 新增模块尚不存在时得到明确失败 `1 failed in 0.02s`；审查回归在修复前也因新增接口缺失得到明确收集错误。
- [x] **步骤 3：实现最小生产代码。** 未新增注册表或工厂；复用了现有物理记录、掩码和有限队列残差实现。
- [x] **步骤 4：在服务器运行精确测试并确认通过。** 审查修复后最后一次相关回归为 `41 passed in 2.06s`。

### 任务 2：冻结配置与服务器包装器

**文件：**

- 新建：`thesis/experiments/llm_probe/configs/ns3_physics_baselines_star_v1.yaml`
- 新建：`thesis/experiments/llm_probe/scripts/run_ns3_physics_baseline.sh`
- 修改：`thesis/experiments/llm_probe/tests/test_ns3_physics_baselines.py`

**固定配置：**

- `hidden_size=128`、`batch_size=64`、`learning_rate=0.001`、`weight_decay=0.0001`、`max_epochs=300`、`patience=30`、`minimum_delta=1e-7`、`lambda_state=1.0`、`lambda_physics=0.01`、`state_supervision_mode=anchor0_plus_one`、`selection_metric=validation_state_mse`、`device=auto`、`cpu_threads=4`。
- 包装器参数仅允许 `constant_state|state_supervision|standard_pinn`、`42|43|44` 和唯一输出目录；运行名由基线语义键、种子和修订号确定，不使用 M 编号。

- [x] **步骤 1：增加配置和包装器合同测试。** 已固定三个语义键、三个种子、四个输入哈希、拓扑、超参数、在线跟踪、运行身份和正式/冒烟目录。
- [x] **步骤 2：实现 YAML 与 Shell 包装器。** 包装器固定从服务端项目根运行，正式与冒烟目录互斥，并复制启动器日志。
- [x] **步骤 3：运行最小验证。** Shell 语法、Python 编译和服务器相关回归均已通过。

### 任务 3：独立审查、服务端冒烟与九次运行

**文件：**

- 新建：`.Codex/docs/sdd/task-ns3-pinn-baselines/implementation-report.md`
- 新建：`.Codex/docs/sdd/task-ns3-pinn-baselines/review.md`
- 新建：`.Codex/docs/sdd/task-ns3-pinn-baselines/experiment-report.md`

- [ ] **步骤 1：格式化与静态检查。** 在服务器执行 `uv run --no-sync black src/flow_probe/ns3_physics_baselines.py tests/test_ns3_physics_baselines.py`、`uv run --no-sync ruff check src/flow_probe/ns3_physics_baselines.py tests/test_ns3_physics_baselines.py`、`uv run --no-sync python -m py_compile src/flow_probe/ns3_physics_baselines.py tests/test_ns3_physics_baselines.py`、`bash -n scripts/run_ns3_physics_baseline.sh`。
- [x] **步骤 2：由新的审查代理检查本任务差异。** 首轮发现重要问题 `4` 项；最小修复后独立复审剩余严重问题 `0`、重要问题 `0`、一般建议 `0`。
- [ ] **步骤 3：服务器两步冒烟。** 三基线不联网真实数据冒烟已通过；在线 SwanLab 冒烟因第三方上传授权门禁尚未执行。
- [ ] **步骤 4：并行启动正式矩阵。** 在不同 `screen` 会话中运行三个语义基线的种子 42、43、44，唯一根目录固定为 `runs/baselines/theory-selection/ns3-star-physics/review-pending-3393d76e-v1/`。
- [ ] **步骤 5：回收并核验。** 比较服务器与本地关键制品 SHA-256，读取九个运行的 `artifact_manifest.json`、`summary.json`、`cost.json` 和 SwanLab 运行信息；云端接口与图表页均需验收。

### 任务 4：汇总与总控写回

**文件：**

- 修改：`.Codex/docs/sdd/task-ns3-pinn-baselines/experiment-report.md`
- 修改：`output/第一创新点实验总控.md`
- 条件修改：`output/开题改进交接文档.md`

- [ ] **步骤 1：汇总三种子。** 对验证和星型测试的完整、已观测、未观测、逐锚点状态均方误差及物理残差均方计算均值、样本标准差和按三个种子计算的 95% t 置信区间；同时报告训练时间、峰值显存、吞吐和推理延迟。
- [ ] **步骤 2：写详细实验报告。** 记录输入与清单哈希、组隔离审计、公式、配置、九次运行指标、日志、服务器与本地路径、SwanLab 运行编号和地址、失败项及 `review_pending` 边界。
- [ ] **步骤 3：更新实验总控。** 只写确定事实、详细报告链接、运行路径和下一门禁；不得把本轮结果写成 R1-R3 胜负或第三章算法冻结。
- [ ] **步骤 4：判断是否修改开题交接。** 只有本轮证据实际改变理论路线、章节边界或长期结论时才精准修改；否则明确记录未修改。

## 自检结果

- 需求覆盖：三类基线、三种子、同输入同掩码、组隔离、只用验证选择、星型边界、SwanLab、完整制品、独立审查、详细报告与总控写回均有对应步骤。
- 占位符检查：计划中无未完成占位标记、待定超参数或结果后选路条款。
- 类型一致性：数据审计、训练选择、测试评价和跟踪入口的输入输出边界互不循环；训练选择接口明确不接收测试集。
- 当前阻塞：只有在线 SwanLab 冒烟、九次正式矩阵、云端复核、结果汇总和正式实验报告被用户外发授权门禁阻塞；本地实现与服务器不联网验证不再阻塞。
