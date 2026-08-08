# 任务十五双锚点最小契约修复独立复核

日期：2026-07-22

## 审查结论

**未发现严重或重要问题。** 当前修复符合任务十五的最小契约：只有 G4R 可使用 `anchor0_plus_one`，其余协调训练变体继续拒绝该模式；状态掩码制品记录运行时实际模式。静态审查未发现协调算法、物理公式、训练预算或既有 G4R 单锚点行为发生回归。

## 审查范围

- `.Codex/docs/2026-07-22-任务十五双锚点协调验证实施计划.md`
- `.Codex/docs/sdd/task-15-dual-anchor-contract-fix-report.md`
- `thesis/experiments/llm_probe/src/flow_probe/game_train.py`
- `thesis/experiments/llm_probe/tests/test_game_train.py`
- 只读核对既有掩码构造器 `build_state_supervision_masks` 的模式语义。

## 契约核对

### 变体准入矩阵

- `_build_settings` 先通过 `_variant_name` 将变体规范化为大写，再检查状态监督模式。
- `game_train.py:1134-1137` 仅在 `settings.variant == "G4R"` 时允许 `{anchor0_only, anchor0_plus_one}`。
- G2、G3、G4、G5、G5-STOP-RESPONSE 的允许集合仍只有 `anchor0_only`；非法模式在模型加载和训练开始前被拒绝。
- `test_settings_accept_g4r_dual_anchor_state_mode` 覆盖 G4R 双锚点准入。
- `test_settings_reject_dual_anchor_for_other_variants` 参数化覆盖其余五个变体。
- 既有 `test_settings_accept_independent_g4r_variant` 继续使用默认 `anchor0_only`，保留 G4R 单锚点准入行为。

### 状态掩码制品

- 训练掩码与验证掩码均使用 `settings.state_supervision_mode` 构造。
- `_write_state_mask` 的 `mode` 已改为必填关键字参数，制品字段不再引用固定常量。
- 唯一生产调用点传入 `settings.state_supervision_mode`，因此掩码构造模式与 `state_mask.json` 记录模式一致。
- 新增测试检查 `mode == anchor0_plus_one`、持久化掩码与构造结果相等，以及每个掩码满足五锚点、`q0` 为真、恰有一个内部锚点为真。

### 回归边界

- `state_supervision_mode` 的生产用途仅限设置校验、训练与验证掩码构造、掩码制品写入、配置快照和训练摘要；未进入协调求解器、协调权重或生成否决逻辑。
- G4R 的私有状态头仍强制接收状态锚点梯度，物理梯度仍由物理接受状态控制，并按物理可靠性缩放。
- G5 与 G5-STOP-RESPONSE 的反应路径仍由变体决定；双锚点模式在进入该路径前即被拒绝。
- 有效生成批量固定为 16、物理批量固定为 4、运行预算固定为 2 或 202 步，相关门禁未因本次模式放宽而改变。
- `state_supervision_mode` 未进入物理残差计算，队列平衡残差及其权重未见变更。

## 验证边界

- 本次仅做静态独立复核，未连接服务器。
- 按任务约束未运行 Ruff、Black、pytest 或任何训练命令。
- `game_train.py` 与 `test_game_train.py` 当前是未跟踪文件，无法通过 Git 基线差异隔离历史改动；本次按目标符号、全部模式使用点和相关调用链逐项核对。
- 服务器精确契约测试仍是最终行为门禁；该未执行项不构成当前静态审查中的严重或重要发现。

## 修改情况

- 新增：`.Codex/docs/sdd/task-15-dual-anchor-contract-review.md`
- 未修改：生产代码、测试、配置、协调算法、物理公式和实验制品。
