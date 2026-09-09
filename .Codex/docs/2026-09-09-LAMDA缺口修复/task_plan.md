# LAMDA 缺口感知条件风险门控回放实施计划

> **给工程代理：** 必须使用 `superpowers:subagent-driven-development` 与 `daily-coding`；本计划是实现要求，数值和接口按原文逐字执行。

**目标：** 在不读取封印年标签的前提下，筛选“恶意缺口感知修复”和“冲突触发双侧风险门控”是否能相对标准经验回放改善 LAMDA 的保持—适应取舍。

**架构：** 复用现有 LAMDA Domain-IL MLP、数据加载器、指标和断点格式，新入口只增加候选损失与条件投影。四个实验臂固定为 ER、ER+缺口修复、ER+条件风险门控、ER+两者联合；所有臂只枚举 `2013/2014/2016/2017`。

**技术栈：** Python、NumPy、PyTorch、Parquet；服务器通过现有 `tools/env/activate.sh` 与 `uv run --no-sync` 运行。

**规格：** `thesis/methods/第三章-LAMDA缺口感知条件风险门控回放候选.md`

## 全局约束

- 数据身份固定为 `IQSeC-Lab/LAMDA` revision `ad9614bdd5556767f97ced2fce797c2f06408ebf`。
- 来源年为 `2013/2014`，开发年为 `2016/2017`，封印年为 `2018--2025`；本筛选不得枚举封印年。
- 发布的 `4561` 维特征空间含未来协变量，本运行必须标记 `screening_only`。
- 总回放容量固定为 `200`，与阶段 A、C 和双风险投影保持同一公平控制变量。
- 固定种子 `42`、每年 `10` 轮、批量 `1024`、既有 SGD 配置和阈值 `0.5`。
- 不修改阶段 A、B、C、双风险投影的既有代码和制品。
- 不运行人工夹具、单元测试或集成测试；只执行语法、配置入口检查和真实源年筛选。
- 不使用未来标签、目标年指标、目标年阈值或目标年模型选择。

## 任务

### Task 1：新增筛查入口与配置

**文件：**
- 新建：`thesis/experiments/llm_probe/tools/ch3_lamda_gap_repair_screening.py`
- 新建：`thesis/experiments/llm_probe/configs/ch3-lamda-gap-repair-screening-v1.json`

**接口：**
- 入口接受 `--config`、`--validate-config`、`--resume`，语义与现有 LAMDA 筛查入口一致。
- 四臂键名为 `experience_replay`、`gap_repair`、`conditional_risk_gate`、`gap_repair_conditional_risk_gate`。
- 输出必须包含逐年预测、逐年指标、训练侧修复／投影计数、断点、输入清单、运行清单和资源收据。

**实现要求：**
- 缺口集合只取当前年度已到达训练区中 `label==1` 且上一冻结模型 `logit < threshold_logit` 的样本。
- 缺口权重为 `max(threshold_logit - old_logit, 0)`；修复损失使用按权重归一化的恶意 BCE；缺口集合为空时修复项为零。
- 参考保护集合只取回放中上一冻结模型已正确判恶意的恶意样本；良性参考集合只取当前年度训练区中上一冻结模型判恶意的良性样本。
- 先形成当前损失、回放损失和缺口修复损失的总梯度；只有总梯度与任一参考梯度内积小于零时，才按固定顺序执行已有 A-GEM 半空间投影；无冲突时保持原梯度。
- 保留现有断点恢复、指标计算、未来年不读取和资源收据语义；不得复制已有脚本后悄悄改变数据或训练预算。

### Task 2：入口与配置检查

- 运行 `uv run --no-sync python tools/ch3_lamda_gap_repair_screening.py --config configs/ch3-lamda-gap-repair-screening-v1.json --validate-config`。
- 运行 `uv run --no-sync python -m py_compile tools/ch3_lamda_gap_repair_screening.py`。
- 运行 `git diff --check`。
- 只在上述检查通过后提交代码变更；不提交或覆盖既有运行制品。

### Task 3：服务器源年筛选

- 使用 `scripts/remote_launchers/launch_run_with_pull.sh` 启动唯一运行身份 `ch3-lamda-gap-repair-screening-seed42-v1`。
- 远端输出目录为 `/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-lamda-gap-repair-screening-seed42-v1`。
- 运行完成后只回收摘要、逐年指标、逐样本预测、断点清单和资源收据；不回收未来年数据。

### Task 4：主代理复算与裁决

- 独立重算四臂 2016/2017 的 AP、AUROC、F1、FPR、FNR、Brier。
- 独立重算旧恶意负向翻转、当前恶意正向修复、良性新增误报和条件投影触发次数。
- 通过条件：相对 ER 不增加 FPR 和旧恶意负向翻转，且 AP、FNR 或恶意正向修复率至少一项改善。
- 联合臂只有在两个单臂均有独立信号且联合不劣于最好单臂时才保留为候选算法；否则缩小为证据更强的单机制或保留 ER 基线。
- 任何候选未通过时不得进入 `2018--2025` 封印评价。

## 状态

当前处于任务 3：入口与配置检查通过，远端源年四臂筛选已启动并由本机回传守护持续同步；等待真实制品。

## 错误记录

- 现有阶段 C 与双风险投影制品保持不变；本计划禁止复用其被否决实现的读数作为新候选证据。
