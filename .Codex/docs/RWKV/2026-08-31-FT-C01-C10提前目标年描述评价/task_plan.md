# FT C01/C10 提前目标年描述评价实施计划

> **执行要求：** 使用既有 FT 目标年描述评价底层函数，以零训练入口评价 C01 与 C10 的 `selected-by-entity` 检查点。

## 目标

新增独立、可机械审计的 LSPR24 描述评价入口，仅消费已完成的 LSPR23 源侧运行，不训练、不选轮、不向源侧反馈，并与程序生成的 XGBoost 和全容量 MLP 目标年基线作同口径比较。

## 文件所有权

- 新建 `thesis/experiments/llm_probe/tools/ch3_ft_c01_c10_lspr24_descriptive_eval.py`
- 新建 `thesis/experiments/llm_probe/configs/ch3-ft-c01-c10-lspr24-descriptive-eval-v1.json`
- 新建 `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_ft_c01_c10_lspr24_descriptive_eval_v1.sh`
- 新建本目录的 `task_plan.md`、`notes.md`、`实施报告.md`
- 不修改现有训练器、评价器、模型、数据视图、基线或其他代理文件

## 阶段

- [x] P0：核对规则、文件所有权与 Git 快照状态
- [x] P0：读取路线合同、现有目标年评价器、完成运行和基线制品接口
- [x] P0：实现零训练编排入口、冻结配置与远程启动器
- [x] P1：执行语法、导入、帮助、配置、`bash -n` 与差异检查
- [ ] P1：补全实施报告，原子提交独占文件并记录提交 SHA

## 强制不变量

- 只评价 C01、C10，不要求也不读取 C00、C11。
- 源运行必须为 `finished`，且模型选择语义为 `selected-by-entity`。
- 源运行目标年读取计数必须为 `0`；本次入口 `training_runs=0`、`optimizer_steps=0`、`parameter_updates=0`。
- LSPR24 只作封印后描述评价，不用于拟合、选轮、阈值或机制反馈。
- 输出实体 AP、逐流 AP、现有口径可得时的最大实体 AP、六档实际 FPR/DR、完整曲线、资源、状态与 manifest。
- 基线比较必须来自当前程序生成表或配置中明确锚定的制品，不混池、不反推缺失指标。
- 目标评价批量仅为披露的工程参数，不改变模型、检查点、样本、标签或指标。

## 验收命令

- `python -m py_compile tools/ch3_ft_c01_c10_lspr24_descriptive_eval.py`
- `python tools/ch3_ft_c01_c10_lspr24_descriptive_eval.py --help`
- `python tools/ch3_ft_c01_c10_lspr24_descriptive_eval.py --config configs/ch3-ft-c01-c10-lspr24-descriptive-eval-v1.json --check-config`
- `bash -n scripts/remote_launchers/run_ch3_ft_c01_c10_lspr24_descriptive_eval_v1.sh`
- `git diff --check -- <六个独占文件>`

## 阻塞条件

- C01/C10 源运行或其 `selected-by-entity` 检查点路径无法从冻结配置机械定位。
- 当前程序生成目标年基线表缺少明确来源、指标口径或 XGBoost/全容量 MLP 条目。
- 现有评价器无法在不读取目标标签的本地验证中完成接口检查。

## 当前状态

**实现与本地静态验收已完成，正在整理实施报告并提交。** 本轮未访问服务器、未读取 LSPR24、未运行真实评价。
