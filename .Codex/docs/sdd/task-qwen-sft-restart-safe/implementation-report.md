# Qwen SFT 可恢复训练实施报告

**日期：** 2026-07-28  
**状态：** 本地实现与静态检查完成，服务器测试待执行

## 结论

Qwen 普通监督微调入口现已具备训练绑定、原子运行状态、最多 20 个优化步一次的完整检查点，以及 Transformers 原生检查点恢复。指定 Shell 包装器现在允许绑定一致的未完成运行从最新完整检查点继续，并在启动前无损归档旧 SwanLab 制品清单。

本轮没有连接服务器、没有运行本地 pytest、没有启动模型或申请 GPU，也没有生成 SwanLab 运行号。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/train_sft.py`
  - 增加 `save_steps=20` 与 `resume_from_checkpoint=auto` 的严格设置校验。
  - 绑定模型路径、训练与验证文件摘要、随机种子、有效批量、训练参数、LoRA 参数和训练代码摘要。
  - 只选择含模型权重、Trainer 状态、优化器、调度器和随机数状态的最高步完整检查点。
  - 原子维护固定字段的 `run_state.json`，并把恢复路径传给 `trainer.train(resume_from_checkpoint=...)`。
- `thesis/experiments/llm_probe/tests/test_train_sft.py`
  - 覆盖设置、绑定、检查点完整性、运行状态转换、异常状态和原生恢复参数。
- `thesis/experiments/llm_probe/scripts/run_genis_hierarchical_qwen.sh`
  - 保留配置、模型、虚拟环境、SwanLab、GPU 和数据盘预检。
  - 新目录正常启动；已有目录先只读校验恢复策略、状态、绑定和完整检查点。
  - `finished`、`failed`、绑定缺失、检查点不完整或恢复策略为 `never` 时，在调用训练命令前退出。
  - 每次启动使用 `launcher.attempt-XXXX.log`，不覆盖历史启动日志。
  - 恢复前把旧 `artifact_manifest.json` 无损归档为 `artifact_manifest.before-attempt-XXXX.json`，避免 SwanLab 因旧清单拒绝同目录续训。
- `thesis/experiments/llm_probe/tests/test_run_genis_hierarchical_qwen_wrapper.py`
  - 使用临时目录和假的 `uv`、`swanlab`、`nvidia-smi`、`df` 验证新运行、三种可恢复状态、拒绝条件、清单归档和日志不覆盖。
- `.Codex/docs/sdd/task-qwen-sft-restart-safe/implementation-report.md`
  - 记录实现边界、静态检查、服务器门禁和遗留风险。

## 未修改范围

- 未修改 TQH 文件、GeNIS 数据与训练实现、其他启动器、历史运行目录和 AGENTS 文件。
- 未执行任务范围外的服务器同步、实验启动、提交或推送。
- 本代理未执行提交或推送；验证期间，共享工作区的外部流程把包装器与测试纳入了现有提交，当前工作树为干净状态。

## 本地验证

- `bash -n thesis/experiments/llm_probe/scripts/run_genis_hierarchical_qwen.sh`
  - 结果：通过。
- `uv run --locked black tests/test_run_genis_hierarchical_qwen_wrapper.py`
  - 结果：通过，文件已格式化。
- `uv run --locked ruff check tests/test_run_genis_hierarchical_qwen_wrapper.py`
  - 首次只发现一个导入排序问题；限定该文件修复后复核通过，输出为 `All checks passed!`。
- `PYTHONPYCACHEPREFIX=/tmp/qwen-sft-wrapper-pycache .venv/bin/python -m py_compile tests/test_run_genis_hierarchical_qwen_wrapper.py`
  - 结果：通过。
- `git diff --check -- <本任务文件>`
  - 结果：通过。
- 本地 pytest
  - 按任务约束未运行。

## 服务器最小门禁

在服务器 `thesis/experiments/llm_probe` 目录运行：

```bash
uv run pytest tests/test_train_sft.py tests/test_run_genis_hierarchical_qwen_wrapper.py -q
bash -n scripts/run_genis_hierarchical_qwen.sh
```

预计耗时 15 至 30 秒。测试使用假的训练与硬件命令，不加载模型、不申请 GPU。

## 服务器与 SwanLab 制品

- 服务器输出路径：未创建。
- 本机运行制品路径：未创建；仅修改上述源码、测试和报告。
- SwanLab 运行号：无。
- SwanLab 运行链接：无。

## 风险与边界

- 只有经指定包装器启动的恢复运行会归档旧 `artifact_manifest.json`。直接执行 `flow-probe-train` 时，跟踪器仍会拒绝含旧清单的目录；这是防止静默覆盖的保守行为。
- 恢复预检只接受 `prepared`、`running`、`interrupted`，并要求至少一个完整检查点。失败运行需要新目录，不能原地复用。
- 新运行在训练入口创建输出目录前，启动日志暂存在输出目录旁。正常退出、错误或可捕获信号会由 EXIT 陷阱移入运行目录；不可捕获的断电可能留下带唯一尝试编号的旁路日志，但不会覆盖历史日志。
- 尚未在服务器真实 `uv` 环境执行 pytest，也未做两步中断恢复冒烟；正式基线启动前必须完成这两项验证和独立代码审查。
