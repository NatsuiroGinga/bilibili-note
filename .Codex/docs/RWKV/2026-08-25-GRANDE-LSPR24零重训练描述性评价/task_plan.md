# GRANDE LSPR24 零重训练描述性评价实施计划

> **执行要求**：本任务由已分派的实现代理按 `writing-plans` 与 `daily-coding` 执行。仓库规则禁止人工夹具、单元测试、集成测试和 `black`，因此以语法、导入、`--help`、配置核验、`bash -n` 和差异检查代替通用测试驱动模板。

**目标：** 不重训且不重新选择 G-A/G-B，对已封印的两个 GRANDE BF16 检查点各执行一次 LSPR24 描述性评价，生成同一口径的排序、运营、首次告警和资源聚合制品。

**架构：** 新工具薄复用 `ch3_grande_protocol_a_source_q0.py` 的候选结构、模型构建和检查点格式，薄复用 `ch3_full_mlp_s0_precision_aggregation_diagnostic.py` 的完整并列组曲线、六档实际可达读数和首次告警聚合。LSPR24 数组在单进程内只加载一遍，每个结构只前向一遍；逐流和逐实体分数只在内存中存活，仅持久化 JSON 摘要与 NPZ 聚合曲线。

**技术栈：** Python 3.10、PyTorch、NumPy、scikit-learn、仓库内 GRANDE 核心、Bash。

**规格来源：** 控制器任务简报；`.Codex/docs/RWKV/RWKV路线总控.md`；`.Codex/docs/RWKV/RWKV第四章恢复卡.md`；`.Codex/docs/RWKV/2026-08-20-可微神经骨干替代XGBoost目标合同.md`。

## 全局约束

- 父运行固定为 `ch3-grande-c00-protocolA-source-q0-seed42-v1-bf16-v1`，只读 G-A/G-B 已封印检查点和选择收据。
- 旧源年 `source_gate` 可以是否决；本任务不使用该门生成候选胜者，也不使用 LSPR24 选择 G-A/G-B。
- LSPR24 是已访问目标年的描述性评价，不是独立测试、正式论文证据或训练选择信号。
- 只使用冻结 `X24` 的 83 个合法字段；原始 IP 只用 `s24/d24` 构造无向实体键，不入模。
- 不训练、不更新参数、不写新检查点；运行收据必须报告 `training_runs=0`、`optimizer_steps=0`、`parameter_updates=0`。
- 两个结构各评价一次并分行报告，不排名、不选胜者、不产生下游训练入口。
- 目标数组单进程只加载一遍，按结构只打分一遍。允许以身份和摘要一致的原子单元收据幂等跳过已完成结构。
- 禁止持久化逐流分数、逐实体分数、逐实体首次告警位置、实体映射或曝光矩阵。
- 本代理不访问服务器、不启动 GPU、不运行真实实验、测试或自动格式化器。

## 文件所有权

- 新建：`thesis/experiments/llm_probe/tools/ch3_grande_lspr24_zero_train_descriptive_eval.py`
- 新建：`thesis/experiments/llm_probe/configs/ch3-grande-lspr24-zero-train-descriptive-eval-bf16-v1.json`
- 新建：`thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_grande_lspr24_zero_train_descriptive_eval_bf16_v1.sh`
- 新建：`.Codex/docs/RWKV/2026-08-25-GRANDE-LSPR24零重训练描述性评价/task_plan.md`
- 新建：`.Codex/docs/RWKV/2026-08-25-GRANDE-LSPR24零重训练描述性评价/notes.md`
- 新建：`.Codex/docs/RWKV/2026-08-25-GRANDE-LSPR24零重训练描述性评价/实施报告.md`
- 不修改：父 GRANDE 工具、父配置、父启动器、路线总控、第四章恢复卡、任何源结果或检查点。

---

### 任务 1：薄评价工具

**交付物：** 一个零训练 CLI，完成父收据绑定、单次目标加载、两结构单次打分、聚合指标与幂等单元发布。

**接口：**

- 输入：`--config <json>`、`--validate-config`、`--resume`。
- 输出：`status.json`、`input-identity.json`、`unit-aggregates/<structure>.json`、`curves/<structure>.npz`、`aggregate-results.json`、`artifact-manifest.json`。
- 复用：`grande.build_model`、`grande.expected_candidates`、`s0.complete_tied_budget_curve`、`s0.actual_reachable_readouts`、`s0.common_integer_fp_budget_readouts`、`s0.first_alert_aggregate`。

- [ ] 读取父配置、选择收据、检查点与摘要，只要 G-A/G-B 都完成即允许描述性评价，不读取源门数值做选择。
- [ ] 用 `np.load` 对 `X24/y24/s24/d24` 各调用一次，构造 47,115 个无向实体和 752 个正实体的冻结自检。
- [ ] 每个结构回载一次检查点，以 BF16 autocast、FP32 sigmoid 按 X24 顺序每流恰好打分一次。
- [ ] 每结构计算逐流 AP、实体 AP、最大池化实体 AP、六档完整并列组实际 FPR/DR、完整曲线、1 基曝光首次告警与资源。
- [ ] 单元 JSON 与 NPZ 先写临时目录后原子发布；`--resume` 只复用身份和曲线摘要一致的完成单元。
- [ ] 聚合表固定两行 G-A/G-B，`selection_performed=false`、`winner=null`、`target_used_for_selection=false`。

### 任务 2：冻结配置与启动器

**交付物：** 独立运行身份、路径、父运行、年度隔离、评价口径、制品政策和资源入场的冻结 JSON 及薄 Bash 包装。

- [ ] 配置固定运行身份、父运行身份、G-A/G-B 结构、LSPR24 四数组、BF16 推理、六档误报预算和首次告警分位。
- [ ] 配置明示拒绝训练、参数更新、新检查点、逐样本制品、目标年选择和正式证据身份。
- [ ] 启动器仅调用资源准入门与新工具，保留日志和原退出码，不自动重试。

### 任务 3：静态验收与实施报告

**验收命令：**

```bash
source tools/env/activate.sh
uv run --no-sync python -m py_compile tools/ch3_grande_lspr24_zero_train_descriptive_eval.py
uv run --no-sync python -c "import tools.ch3_grande_lspr24_zero_train_descriptive_eval"
uv run --no-sync python tools/ch3_grande_lspr24_zero_train_descriptive_eval.py --help
uv run --no-sync python tools/ch3_grande_lspr24_zero_train_descriptive_eval.py --config configs/ch3-grande-lspr24-zero-train-descriptive-eval-bf16-v1.json --validate-config
bash -n scripts/remote_launchers/run_ch3_grande_lspr24_zero_train_descriptive_eval_bf16_v1.sh
git diff --check -- <本任务六个文件>
```

- [ ] 语法、导入、`--help`、配置核验、`bash -n` 和差异检查全部通过。
- [ ] 实施报告记录已修改文件、未修改范围、通过命令、未运行真实实验和剩余风险。
- [ ] 只暂存并提交本任务的 6 个独占文件，不夹带工作树中的他人改动。

## 错误记录

- 暂无。

## 状态

**当前执行任务 1**：已完成恢复与薄复用边界核对，正在实现零训练评价入口。
