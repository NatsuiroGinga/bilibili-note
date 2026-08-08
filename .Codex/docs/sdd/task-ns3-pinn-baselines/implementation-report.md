# 星型 ns-3 同协议物理基线实现报告

- **状态日期**：2026-07-24。
- **任务状态**：实现、审查修复、独立复审、服务器回归和不联网真实数据冒烟已完成；在线 SwanLab 冒烟与正式九次运行等待用户外发授权。
- **实施计划**：[implementation-plan.md](implementation-plan.md)。
- **输入审计**：[notes.md](notes.md)。

## 1. 实现范围

| 文件                                                                      | 变更                                                                                                                                            |
| ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `thesis/experiments/llm_probe/src/flow_probe/ns3_physics_baselines.py`    | 新增星型 ns-3 三基线统一入口、哈希与组隔离审计、训练集变换、常数预测器、共享状态回归器、标准 PINN 残差、验证选择、测试评价、成本和 SwanLab 制品 |
| `thesis/experiments/llm_probe/tests/test_ns3_physics_baselines.py`        | 新增输入泄漏、常数可见范围、同初始化、唯一物理变量、可微梯度、测试选择边界、配置、包装器和制品合同测试                                          |
| `thesis/experiments/llm_probe/configs/ns3_physics_baselines_star_v1.yaml` | 冻结星型输入哈希、训练预算、损失权重、设备自动选择和 SwanLab 在线配置                                                                           |
| `thesis/experiments/llm_probe/scripts/run_ns3_physics_baseline.sh`        | 新增服务端单基线、单种子、唯一输出目录包装器，支持正式档与最多两轮的冒烟档                                                                      |
| `thesis/experiments/llm_probe/pyproject.toml`                             | 新增 `flow-probe-ns3-physics-baseline` 控制台入口；保留所有既有未提交改动                                                                       |

未修改 `runs/ns3-data/`、TQH-C2、GeNIS、R1/R2/R3 候选、既有 Qwen 训练实现和任何原始数据。

## 2. 三基线合同

### 2.1 共享部分

- 输入只包含四窗口五个公共字段：链路起始容量、结束容量、配置容量积分、队列规则接收字节和接收包数。
- 状态目标是以四窗口最大配置容量积分为公共尺度归一化的五个非负队列锚点。
- 状态监督固定为按完整 `group_id` 生成的 `anchor0_plus_one` 掩码。
- 两个神经基线都使用 `Linear(20,128) → SiLU → Linear(128,128) → SiLU → Linear(128,5) → Softplus`。
- 同一随机种子下，两个神经基线共享初始权重、训练样本、掩码、批次生成方法、AdamW 配置、状态损失、最大轮数、早停规则和验证选择指标。
- 输入标准化均值和标准差只由训练集拟合；模型选择只使用验证完整状态均方误差。
- 测试集不传入 `train_selected_model`，只在最佳验证权重固定后评价一次。

### 2.2 唯一处理变量

- `constant_state`：逐锚点仅使用训练掩码可见真值计算常数，不训练神经网络。
- `state_supervision`：只优化掩码可见锚点的状态均方误差，物理权重实际为 `0`。
- `standard_pinn`：在完全相同的状态监督上额外加入 `lambda_physics=0.01` 的现有单尺度有限队列守恒残差均方，不增加输入字段或模型参数。

标准 PINN 残差为：

```text
[s(q̂[k+1]-q̂[k]) - A[k] + D[k] + L_before[k] + L_after[k]] / C[k]
```

其中预测状态 `q̂` 位于残差计算图中，测试已确认物理项对预测状态的梯度非零。

## 3. 测试驱动证据

### 3.1 红灯

生产模块不存在时，先同步最小测试并在服务器执行：

```bash
uv run --no-sync pytest -q tests/test_ns3_physics_baselines.py
```

结果：`1 failed in 0.02s`。失败是明确断言 `flow_probe.ns3_physics_baselines` 不存在，不是导入环境、语法或依赖错误。

### 3.2 首轮绿灯与根因修复

实现后首轮相关回归结果为 `1 failed, 36 passed in 2.11s`。唯一失败是额外输入字段被底层 `PhysicsDataError` 正确拒绝，但统一入口没有把该异常转换为 `Ns3PhysicsBaselineError`。

按 `systematic-debugging` 与 `bug-detective` 追踪后，根因定位到 `_load_split` 的组件边界未统一异常类型。最小修复是在该边界捕获 `PhysicsDataError` 并保留异常链转换；没有修改测试、输入合同或科学公式。

原失败节点复核：

```text
1 passed in 1.21s
```

相关完整回归：

```text
37 passed in 2.18s
```

### 3.3 格式化后最终相关回归

服务器命令：

```bash
uv run --no-sync pytest -q tests/test_ns3_physics_baselines.py tests/test_physics_train.py -W error::UserWarning
uv run --no-sync python -m py_compile src/flow_probe/ns3_physics_baselines.py tests/test_ns3_physics_baselines.py
bash -n scripts/run_ns3_physics_baseline.sh
```

初版结果：`37 passed in 1.98s`；Python 编译和 Shell 语法检查退出码均为 `0`。独立审查修复后最后一次结果为 `41 passed in 2.06s`，Python 编译和 Shell 语法检查再次通过。

## 4. 格式化与静态检查

- `black` 已实际格式化两份新增 Python 文件。
- `ruff check` 首次报告两个未使用的 SwanLab 常量导入；确认它们不参与执行后做了单点删除。审查修复后的最终 Ruff 检查只报告测试导入顺序，已做单点排序修复。
- 按局部规则，Ruff 缺陷修复后只重新执行 Python 编译、Shell 语法和直接相关回归，没有重复运行 Ruff。
- `prettier --write` 已处理冻结 YAML；YAML 内容无需改写。
- `bash -n` 已通过包装器语法检查。

## 5. 本地与服务器同步验收

代码同步使用 `rsync --relative` 白名单，不使用 `--delete`，未传输运行制品、数据集、模型、环境或凭据。

| 文件                                         | 本地与服务器共同 SHA-256                                           |
| -------------------------------------------- | ------------------------------------------------------------------ |
| `src/flow_probe/ns3_physics_baselines.py`    | `3cd72d376a3e06cd706cc1334ee7c6f1e8974a56d54a797318691bf9728793ef` |
| `tests/test_ns3_physics_baselines.py`        | `a2d69992085b1581416be9aea88a68acca19ffd14fe489d679d3f37f49e563d7` |
| `configs/ns3_physics_baselines_star_v1.yaml` | `09196a82056d2f0e63cdb73300051b5f8107dc8048c68143ce9b052252d77592` |
| `scripts/run_ns3_physics_baseline.sh`        | `1e341848b333e3b8b4b260ba772c28965d3bd26e6118be2cda7b681fb801e878` |
| `pyproject.toml`                             | `b53f48293a8f21eea524f05bafd49fbbb80fe281abc5c161333234183a524365` |

服务端只执行了 `uv pip install --no-deps -e .` 刷新控制台入口，没有运行裸 `uv sync`，也没有移除或重建训练依赖。

## 6. 不联网真实数据冒烟

在线 SwanLab 冒烟在远程命令执行前被安全审批拒绝，因此没有创建运行目录、SwanLab 运行或正式制品。审批原因是运行会把配置、指标、日志和制品元数据发送到第三方工作区；在用户知情明确授权前不得绕过。

随后执行了不联网、不上传、不写正式结果的真实星型数据两轮训练冒烟。结果为：

| 基线                | 最佳轮 | 完成轮数 | 设备 | 参数量 |
| ------------------- | -----: | -------: | ---- | -----: |
| `constant_state`    | 不适用 |   不适用 | CPU  |      0 |
| `state_supervision` |      2 |        2 | CUDA | 19,845 |
| `standard_pinn`     |      2 |        2 | CUDA | 19,845 |

同次运行重新确认三个划分各 807 条、各 7 组，样本与组交集均为 0，输入字段数为 5，拓扑唯一为 `star-bottleneck-v1`。三基线都在常数或最佳权重冻结后才物化 807 条测试样本，测试不进入拟合或验证选择。

## 7. 独立审查与复审

首轮独立审查为严重问题 `0`、重要问题 `4`，定位到测试集过早物化、完成状态过早、SwanLab 最终步数可能倒退、正式与冒烟身份隔离不足。修复没有改动模型结构、物理公式、输入字段、超参数或划分，只调整运行编排和证据门禁：

1. 训练前只流式审计测试标识与公共五字段；测试状态和通量在选择结果返回且类型校验通过后才物化。
2. 普通运行只进入 `awaiting_tracking_verification`；人工记录云端可见指标和图表并再次完成本地制品检查后，单独的复核命令才允许写入 `finished`。
3. 最终跟踪步骤改为 `len(history) + 1`，常数基线固定为步骤 `1`。
4. 正式与冒烟运行具有不同目录根、运行类型、有效轮数、协议完整性字段和 SwanLab 标签。

独立复审结论为剩余严重问题 `0`、重要问题 `0`、一般建议 `0`，四项原问题全部关闭。报告见 [review.md](review.md)。

## 8. 已知边界

1. 当前输入是既有星型数据，而不是尚未发布的完整 `dataset-v1`，因此所有后续结果只能标记为 `theory_selection/review_pending`。
2. 本轮只验证单尺度有限队列标准 PINN，不包含多尺度、TCP 流体、网络演算、有界注意力或路由专家。
3. 星型测试分区已在历史实验中使用过，不能视为全新最终测试；本轮只用于同协议物理基线复核。
4. 九次正式运行、SwanLab 云端图表验收和制品回收尚未在本报告状态下完成。
5. 在线冒烟和正式矩阵被第三方数据外发授权门禁阻塞；获得用户明确授权后才能继续。

## 9. 总控写回

- 已更新 `output/第一创新点实验总控.md`，记录三基线实现、服务器验证、独立复审、当前授权门禁和不得据此裁决 R1、R2、R3 的边界。
- 未修改 `output/开题改进交接文档.md`。本轮没有改变课题定位、第三四章关系、章节结构或长期理论边界。
- 未创建正式 `experiment-report.md`。九次正式运行尚未执行，现阶段不能生成指标汇总或伪造实验结论。
