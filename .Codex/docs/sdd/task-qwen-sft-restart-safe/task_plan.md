# Qwen SFT 可恢复训练实施计划

> **代理执行要求：** 必须使用 `superpowers:subagent-driven-development` 逐项实现；实现代理可按实验目录局部规则针对本任务使用一次 `superpowers:test-driven-development`。

**目标：** 使即将用于统一 `dataset-v1` 基线的 `qwen_sft` 在服务器关机后能够验证输入绑定并从最近完整检查点继续，而不覆盖已完成或不兼容的运行。

**架构：** 保留现有 TRL `SFTTrainer`，把保存策略从按轮改为最多每 20 个优化步保存，并使用 Transformers 原生检查点恢复模型、优化器、调度器和随机数状态。训练入口额外维护原子写入的 `training_binding.json` 与 `run_state.json`；Shell 包装器只允许恢复绑定一致且存在完整检查点的未完成目录。

**技术栈：** Python 3.10、TRL、Transformers、PEFT、PyTorch、YAML、Bash、pytest、Black、Ruff。

## 全局约束

- 只修改普通监督 Qwen 入口，不改已经结束的物理训练结果或历史运行目录。
- 检查点间隔固定不超过 20 个优化步；配置允许更小正整数，不允许大于 20。
- 恢复时训练数据、验证数据、模型、随机种子、科学超参数和代码绑定必须一致。
- 硬件降级参数可以变化，但有效批量、步数、种子、样本清单和科学超参数不能变化。
- 服务器上的所有检查点、状态和日志必须位于 `/root/autodl-tmp/thesis/`。
- Python 测试只在服务器 `uv` 环境运行；本机只做代码审阅与 Markdown 格式化。
- 不提交、不推送，不修改用户及其他代理的无关改动。

---

### 任务 1：冻结训练绑定并选择最近完整检查点

**文件：**

- 修改：`thesis/experiments/llm_probe/src/flow_probe/train_sft.py`
- 修改：`thesis/experiments/llm_probe/tests/test_train_sft.py`

**接口：**

- `TrainingSettings.save_steps: int`，默认 `20`，合法范围 `1..20`。
- `TrainingSettings.resume_from_checkpoint: str`，只接受 `"auto"` 或 `"never"`，默认 `"auto"`。
- `build_training_binding(probe: ProbeConfig, settings: TrainingSettings, model_path: Path) -> dict[str, object]`：返回模型标识、模型路径、种子、训练与验证文件 SHA-256、批量、累积步数、学习率、轮数、最大步数、长度限制和 LoRA 设置。
- `resolve_resume_checkpoint(output_dir: Path, expected_binding: Mapping[str, object], resume_policy: str) -> Path | None`：只从绑定一致的未完成目录选择步数最大的完整 `checkpoint-<step>`。

- [ ] **步骤 1：增加设置解析测试**

  在 `test_train_sft.py` 增加断言：缺省值为 `save_steps=20` 与 `resume_from_checkpoint="auto"`；`save_steps` 为 `0`、`21` 或非整数时拒绝；恢复策略不是 `auto/never` 时拒绝。

- [ ] **步骤 2：增加绑定稳定性测试**

  使用临时训练与验证 JSONL，证明相同输入得到相同绑定；改变任一文件内容、随机种子、学习率、有效批量、LoRA 参数或模型路径都会改变绑定。

- [ ] **步骤 3：增加检查点完整性测试**

  构造 `checkpoint-20` 与 `checkpoint-40`。完整检查点必须同时含 `trainer_state.json`、`optimizer.pt`、`scheduler.pt`、`rng_state.pth`，以及 `adapter_model.safetensors` 或 `model.safetensors`；最高步检查点缺任一文件时回退到前一个完整检查点。绑定不一致、状态为 `finished`、策略为 `never` 或目录中没有完整检查点时不得恢复。

- [ ] **步骤 4：实现纯函数与原子 JSON 写入**

  在 `train_sft.py` 中实现文件 SHA-256、规范化绑定摘要、临时文件加 `Path.replace()` 的 JSON 原子写入，以及上述检查点选择函数。异常信息必须指出具体缺失文件或绑定字段。

- [ ] **步骤 5：运行服务器最小测试**

  运行：

  ```bash
  uv run pytest tests/test_train_sft.py -q
  ```

  预期：全部通过，且不加载模型、不申请 GPU。

### 任务 2：接入原生恢复与运行状态

**文件：**

- 修改：`thesis/experiments/llm_probe/src/flow_probe/train_sft.py`
- 修改：`thesis/experiments/llm_probe/tests/test_train_sft.py`

**接口：**

- `run_state.json` 字段固定为 `schema_version`、`run_id`、`status`、`current_step`、`latest_checkpoint`、`binding_sha256`、`swanlab_run_id`、`started_at`、`updated_at` 和 `failure`。
- 状态只允许 `prepared`、`running`、`interrupted`、`failed` 与 `finished`。
- `RestartStateCallback` 在训练开始、保存检查点和训练结束后原子更新状态。

- [ ] **步骤 1：增加状态转换测试**

  使用假的 Trainer 控制对象验证 `prepared -> running -> finished`；保存事件把当前步和最近检查点写入状态；`KeyboardInterrupt` 写 `interrupted`，普通异常写 `failed`，异常文本写入 `failure`。

- [ ] **步骤 2：增加恢复参数测试**

  替换假的 Trainer，验证新运行调用 `trainer.train(resume_from_checkpoint=None)`，恢复运行调用 `trainer.train(resume_from_checkpoint=".../checkpoint-40")`，已完成目录和绑定不一致目录在加载模型前失败。

- [ ] **步骤 3：接入步级保存策略**

  将 `SFTConfig` 固定为 `save_strategy="steps"`、`save_steps=settings.save_steps`、`save_total_limit=3`、`save_only_model=False`，保持 `logging_steps=1`。不得改变优化器、学习率、有效批量、种子或数据顺序。

- [ ] **步骤 4：写入绑定和运行状态**

  首次运行先创建输出目录并写 `training_binding.json`、配置快照和 `run_state.json`。恢复运行先验证绑定和检查点，再加载模型。训练完成后继续保存 `final_adapter` 与 `training_summary.json`，并把状态改为 `finished`。

- [ ] **步骤 5：运行服务器最小测试**

  运行：

  ```bash
  uv run pytest tests/test_train_sft.py -q
  ```

  预期：全部通过；测试证明恢复参数、状态转换和不覆盖规则有效。

### 任务 3：让 Shell 包装器安全恢复

**文件：**

- 修改：`thesis/experiments/llm_probe/scripts/run_genis_hierarchical_qwen.sh`
- 新建：`thesis/experiments/llm_probe/tests/test_run_genis_hierarchical_qwen_wrapper.py`
- 修改：`thesis/experiments/llm_probe/AGENTS.md`
- 新建：`.Codex/docs/sdd/task-qwen-sft-restart-safe/implementation-report.md`

**接口：**

- 新目录正常启动。
- 已有目录只有在 `run_state.json` 为 `prepared`、`running` 或 `interrupted`，配置恢复策略为 `auto`，且 Python 入口能找到完整检查点时才允许继续。
- `finished`、`failed`、缺绑定或缺完整检查点的目录拒绝复用。
- 每次启动器日志使用唯一尝试编号写入输出目录，不覆盖以前日志。

- [ ] **步骤 1：增加包装器行为测试**

  用临时目录和假的 `uv`、`swanlab`、`nvidia-smi` 命令验证：新运行可启动；完整中断目录可恢复；完成目录、失败目录、绑定缺失目录和无完整检查点目录均拒绝；第二次启动不会覆盖第一次启动日志。

- [ ] **步骤 2：修改包装器预检**

  保留模型、配置、虚拟环境、SwanLab、GPU 和磁盘检查。删除“输出目录存在即一律拒绝”的旧判断，改为调用 Python 入口的只读恢复预检；所有日志继续写入持久化运行目录。

- [ ] **步骤 3：执行服务器验证**

  运行：

  ```bash
  uv run pytest tests/test_train_sft.py tests/test_run_genis_hierarchical_qwen_wrapper.py -q
  bash -n scripts/run_genis_hierarchical_qwen.sh
  ```

  预期：全部通过。

- [ ] **步骤 4：做两步中断恢复冒烟**

  使用独立冒烟输出目录运行到第 2 步后正常中断，确认检查点、绑定和状态完整；重新执行同一命令后从第 2 步继续到第 3 步。验证最终全局步为 3、步骤指标不重复、学习率连续、第一次日志仍保留。该冒烟不得使用正式 `dataset-v1` 测试清单。

- [ ] **步骤 5：集中交付检查**

  只对本任务修改文件执行一次 Black、Ruff、`bash -n`、Prettier 和 `git diff --check`。将命令、结果、SwanLab 运行号、服务端输出路径、本机归档路径和遗留风险写入实现报告；新增“恢复前必须校验绑定与完整检查点”的防复发规则。

## 验收门槛

1. 服务器关机后可以从最近完整的 20 步内检查点恢复模型、优化器、调度器和随机数状态。
2. 绑定不一致、已完成、失败或不完整运行不会被静默续跑或覆盖。
3. 恢复前后全局步、学习率和样本顺序连续，步骤指标不重复。
4. 配置、状态、检查点和每次启动日志均位于持久化运行目录。
5. 实现报告与实验 AGENTS 防复发规则落盘；独立代码审查严重问题和重要问题均为 0 后，才允许启动正式 `qwen_sft` 基线。
