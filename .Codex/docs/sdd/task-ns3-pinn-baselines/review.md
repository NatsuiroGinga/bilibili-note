# 星型 ns-3 同协议物理基线独立复审

## 结论

- 复审裁决：**四项原重要问题均已关闭，可以进入后续正式运行门禁**。
- 剩余严重问题：**0**。
- 剩余重要问题：**0**。
- 一般建议：**0**。
- 审查边界：本次只静态复核当前生产代码、测试与包装脚本；未运行测试、训练或服务器命令，除本报告外未修改任何文件。

## 逐项复审

### 1. 测试集延迟物化：已关闭

训练前的 `audit_star_split_inputs` 只保留测试集标识，并校验公共五字段，不调用 `prepare_physics_record`，因此不会构造包含状态真值与物理通量的测试 `PhysicsSplit`：`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:273`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:348`。

正式入口只先物化训练集和验证集；`select_then_materialize_test` 严格按“选择回调返回、选择结果类型校验通过、物化测试集”的顺序执行：`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:475`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1258`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1382`。神经选择结果采用冻结数据类 `SelectedModel`，正式调用明确执行类型检查：`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:151`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1394`。行为测试还验证了加载事件顺序及类型校验失败时不会加载测试集：`thesis/experiments/llm_probe/tests/test_ns3_physics_baselines.py:203`。

### 2. 完成状态与制品门禁：已关闭

`run_status_payload` 禁止在 `tracking_verified=False` 时生成 `finished` 状态：`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:872`。普通运行在 SwanLab 上下文退出、复核占位记录写入、文件哈希生成和本地制品检查后只进入 `awaiting_tracking_verification`，任一异常都会改写为 `crashed`：`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1524`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1549`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1563`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1569`。

人工云端复核入口先校验运行编号、可见指标、可见图表、证据说明、SwanLab 原始日志和全部本地制品；只有复核记录写入并再次通过本地校验后才写 `finished`，后续校验失败仍会改写为 `crashed`：`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1082`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1120`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1165`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1170`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1191`。

### 3. SwanLab 最终步数：已关闭

`final_tracking_step` 对神经基线固定返回 `len(history) + 1`，并校验最佳轮次属于历史范围；无训练历史的常数基线返回首步。正式入口统一使用该函数写最终指标：`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:861`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1508`。测试覆盖“最佳轮次早于历史末轮”的情况：`thesis/experiments/llm_probe/tests/test_ns3_physics_baselines.py:450`。

### 4. 正式与冒烟身份及目录隔离：已关闭

`build_run_identity` 强制生成 `run_kind`、`effective_max_epochs` 和 `protocol_complete`，并拒绝正式运行覆盖轮数或冒烟运行缺少轮数：`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:808`。`validate_output_location` 将正式运行限制到固定的基线与种子目录，将冒烟运行限制到独立冒烟根目录：`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:832`。

运行身份已进入配置快照、SwanLab 标签与元数据、汇总、成本和运行状态：`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1216`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1273`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1300`、`thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py:1447`。包装脚本也在调用 Python 前独立执行相同目录隔离，并显式传递 `--run-kind`：`thesis/experiments/llm_probe/scripts/run_ns3_physics_baseline.sh:36`、`thesis/experiments/llm_probe/scripts/run_ns3_physics_baseline.sh:86`。对应测试覆盖身份组合和交叉目录拒绝：`thesis/experiments/llm_probe/tests/test_ns3_physics_baselines.py:379`、`thesis/experiments/llm_probe/tests/test_ns3_physics_baselines.py:401`。

## 验证证据与边界

- 委托方提供的服务器证据：目标测试 **41 passed**；三个基线的无联网真实数据冒烟均通过。
- 本复审未独立重跑上述命令，因此只确认代码路径与现有证据一致，不把该测试结果表述为本代理复现结果。
- 每次真实正式运行仍须完成对应的人工 SwanLab 云端指标与图表复核，生成 `tracking_verification.json` 的 `verified` 状态后，才允许把该次运行视为 `finished`；这是现有代码已经实施的运行门禁，不是剩余代码问题。
