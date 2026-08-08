# 共享 B0 HGB/XGBoost 正式基线 v2 修复与重跑报告

## 结论

三项独立审查问题已完成有界修复，`v2` 正式运行于 2026-07-30 正常结束。HGB 与 XGBoost 已由两个全新 Python 进程分别训练和评价；启动日志、原子状态、真实退出码、代码与输入绑定、服务器能力、两个模型子运行及全部制品均归入唯一运行根目录并登记大小与 SHA-256。

`v2` 与 `v1` 的输入合同相同，合并预测解压后逐字节相同，排除推理耗时与吞吐字段后的全部检测指标逐项相同。因此本轮只修复内存与运行证据，不改变科学结果。运行继续标记为 `theory_selection/review_pending`。

## 修复范围

修改文件：

- `thesis/experiments/llm_probe/src/flow_probe/shared_b0_tabular_baselines.py`
- `thesis/experiments/llm_probe/tests/test_shared_b0_tabular_baselines.py`
- `thesis/experiments/llm_probe/scripts/run_shared_b0_tabular_baselines.sh`
- `thesis/experiments/llm_probe/scripts/AGENTS.md`
- `.Codex/docs/sdd/task-shared-b0-tabular-baselines/task_plan.md`
- `output/第一创新点实验总控.md`

未修改数据清单、公共字段、标签合同、HGB/XGBoost 参数、随机种子、评价指标、SwanLab 项目、Qwen 结果或 `v1` 目录。

## 根因与修复

### 1. 逐模型内存不可比较

- 根因：旧入口在同一进程中先后运行两个模型，`ru_maxrss` 是不可重置的进程生命周期高水位。
- 修复：父入口只负责合同核对、SwanLab 跟踪和结果汇总；HGB 与 XGBoost 分别由全新的子进程独立加载同一冻结输入、训练、评价和记录峰值常驻内存。
- 证据：两个子运行进程号分别为 `20484` 与 `20639`，互不相同；成本文件明确记录测量范围 `isolated_single_model_process_end_to_end`。

### 2. 启动证据不在唯一运行目录

- 根因：旧 Shell 将启动日志、状态、退出码、绑定和能力清单写在运行目录同级，且未进入制品清单。
- 修复：Shell 先创建唯一 `v2` 根目录，所有启动证据从第一步起写入该目录；两个模型各有独立 `model-runs/<模型>/` 子目录和制品清单。成功结束后，最终化入口递归登记根目录内全部普通文件的相对路径、大小和 SHA-256。
- 证据：最终清单登记 `38` 个文件，重新计算后大小与 SHA-256 全部一致。

### 3. 预检失败缺少可靠状态

- 根因：旧入口在首次状态落盘前执行命令能力和哈希预检，`set -e` 可导致无状态退出。
- 修复：创建根目录后立即原子写入 `prepared`，正式预检前切换为 `running`，并安装统一 `EXIT` 陷阱；任何未完成退出都会写入 `failed` 和真实退出码。
- 防复发发现：当 Python 静默返回 `7` 时，首次实现的空日志门禁把退出码覆盖为 `1`。现已改为补写空日志诊断但保留原始非零码；只有前序命令与 `tee` 都成功而日志仍为空时才使用通用失败码。规则已写入 `scripts/AGENTS.md`。

## 最小验证

服务器首次只运行 6 个直接目标测试和 Shell 语法检查：

- `bash -n scripts/run_shared_b0_tabular_baselines.sh`：通过。
- 目标测试：`5 passed, 1 failed`。
- 唯一失败：静默 Python 退出 `7` 被空日志门禁覆盖为 `1`。

单点修复后只重跑原失败节点：

- `tests/test_shared_b0_tabular_baselines.py::test_launcher_preserves_python_failure_exit_code`：`1 passed in 1.02s`。
- `bash -n scripts/run_shared_b0_tabular_baselines.sh`：通过。

本机未运行 `pytest`。Python 语法预检首次因系统默认字节码缓存目录受沙箱限制而失败，设置 `PYTHONPYCACHEPREFIX=/tmp/pycache-shared-b0-v2` 后两文件语法预检退出码为 `0`。

## 正式运行

- 服务端根目录：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/baselines/shared-b0-tabular-seed42-theory-selection-review-pending-v2/`
- 启动日志：上述目录的 `launcher.log`
- 启动状态：上述目录的 `launcher-state.json`，最终为 `finished`
- 退出码：上述目录的 `launcher-exit-code.txt`，值为 `0`
- 总制品清单：上述目录的 `artifact_manifest.json`
- HGB 子运行：上述目录的 `model-runs/hgb/`
- XGBoost 子运行：上述目录的 `model-runs/xgboost/`
- 验收脚本：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/verification/shared-b0-tabular-v2/verify.py`
- SwanLab 项目：`mortiswang/malicious-traffic-llm`
- SwanLab 运行号：`dfmrf3ra`
- SwanLab 地址：`https://swanlab.cn/@mortiswang/malicious-traffic-llm/runs/dfmrf3ra/chart`

## 检测指标

| 模型    | 验证集 | 宏平均 F1 | 良性误报率 | 攻击召回率 | 与 v1 检测指标 |
| ------- | ------ | --------: | ---------: | ---------: | -------------- |
| HGB     | GeNIS  |  0.970704 |   0.093400 |   1.000000 | 逐项相同       |
| HGB     | TQH-C2 |  0.884430 |   0.094697 |   0.954327 | 逐项相同       |
| XGBoost | GeNIS  |  0.971978 |   0.089485 |   1.000000 | 逐项相同       |
| XGBoost | TQH-C2 |  0.896475 |   0.081439 |   0.951923 | 逐项相同       |

额外一致性证据：

- `v1/v2` 输入合同完全相同。
- `v1/v2` 合并预测解压后逐字节相同。
- 仅推理耗时和吞吐因独立进程重跑而变化，不属于检测指标差异。

## 成本与内存

| 模型    | 训练耗时/秒 | 峰值常驻内存/字节 | 峰值常驻内存/MiB | GeNIS 吞吐/样本每秒 | TQH-C2 吞吐/样本每秒 |
| ------- | ----------: | ----------------: | ---------------: | ------------------: | -------------------: |
| HGB     |    0.324932 |         781512704 |          745.309 |           85899.230 |            74003.140 |
| XGBoost |    0.292295 |         858783744 |          819.000 |          298983.464 |           281746.351 |

该内存口径是每个独立模型进程从解释器启动、依赖导入、冻结数据加载到训练与评价结束的端到端进程高水位，不能解释为仅模型对象的增量内存。

## SwanLab 云端验收

- `run info` 返回 `state=FINISHED`，配置中的阶段为 `theory_selection`、状态为 `review_pending`、种子为 `42`、执行隔离为 `one_fresh_process_per_model`。
- `run summary` 返回完整标量摘要。
- `run metrics` 对四个指定键均返回一个第 `0` 步数据点：XGBoost 的 GeNIS/TQH-C2 宏平均 F1 分别为 `0.9719783339355876`、`0.8964745412484684`，HGB/XGBoost 峰值常驻内存分别为 `781512704`、`858783744` 字节。
- 云端数值与本地 `summary.json`、`cost.json` 一致。

## 局限性

- 本轮只解决三项审查缺陷，没有重新审查方法选择或数据协议。
- 逐模型内存现在可在本轮同硬件、同入口、同输入下比较，但仍是单次端到端高水位；若论文需要稳定的效率误差范围，正式验证阶段应增加独立重复。
- 运行仍为 `theory_selection/review_pending`，不能进入论文最终主表。
