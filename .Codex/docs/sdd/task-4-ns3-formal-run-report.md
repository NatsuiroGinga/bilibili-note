# 任务 3：正式 ns-3 矩阵与 SwanLab 跟踪实现报告

## 结论

- 正式矩阵运行器、命令入口和服务器包装脚本已经实现。
- 服务器目标测试、完整回归、Shell 语法、ns-3 编译和两场景在线冒烟均已通过。
- 正式七场景、三随机种子矩阵已经完成：21 个组全部成功，共 2520 个窗口，双残差非零窗口为 0。
- SwanLab 运行 `qd8cw9ap` 的云端状态为 `FINISHED`，6 个标量键均记录至最终 `step=22`，图表页已完成验收。
- 正式矩阵、冒烟和测试目录均已从服务器完整同步到本地同名路径，本地只读复核通过。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/ns3_experiment.py`
- `thesis/experiments/llm_probe/tests/test_ns3_experiment.py`
- `thesis/experiments/llm_probe/scripts/run_ns3_queue_truth_matrix.sh`
- `thesis/experiments/llm_probe/pyproject.toml`
- `.Codex/docs/sdd/task-4-ns3-formal-run-report.md`

未修改任务 1 的 C++ 生成器与 `ns3_truth.py`，未修改任务 2 的字段角色配置或实现，未执行 Git 提交、推送或远程配置。

## 实现接口

- 命令入口：`flow-probe-run-ns3-matrix = "flow_probe.ns3_experiment:main"`。
- Python 入口：`run_ns3_matrix(...)`。
- 固定场景顺序：`benign-low`、`benign-high`、`benign-capacity-shift`、`benign-random-loss`、`dos-udp-medium`、`dos-udp-high`、`dos-udp-capacity-shift`。
- 默认随机种子：42、43、44；每个组合的 `run` 固定为 1。
- 服务器脚本：`scripts/run_ns3_queue_truth_matrix.sh`。脚本先加载 `~/.bashrc`，再启用 `set -u`，并加入隔离 CMake 路径。
- 每个组合使用 `subprocess` 参数列表调用 `env USER=ns3builder <ns3>/ns3 run ...`，不启用 `shell=True`。
- 每组生成后单独调用 `validate_ns3_truth_paths([csv_path])`；全部完成后再对完整 CSV 列表执行汇总验证。
- 保存的 L3 与包级零残差只用于生成器审计，不进入训练损失。

## 制品契约

每次运行拒绝任何已经存在的输出目录。新目录创建后立即写入配置和阶段状态，并持续更新：

- `config_snapshot.json`
- `environment_snapshot.json`
- `source_sha256.json`
- `csv_sha256.json`
- `group_status.json`
- `run_status.json`
- `validation_summary.json`
- `swanlab_metrics.json`
- `console.log`
- `csv/*.csv`
- `logs/*.stdout.log`
- `logs/*.stderr.log`
- `swanlog/ns3-matrix/`
- `artifact_manifest.json`

SwanLab 固定使用在线模式、工作区 `mortiswang`、项目 `malicious-traffic-llm`。每个组使用递增步骤记录累计完成组数、失败组数、窗口数、队列丢弃 L3 字节、下游随机误码 PPP 帧字节和双残差非零窗口数；最后增加一次汇总步骤。

## 测试驱动记录

本任务只在首次实现前读取和使用一次测试驱动开发技能，后续未再次读取或启用。

### 红测

服务器项目：`/root/autodl-tmp/thesis/experiments/llm_probe`

命令：

```bash
uv run --no-sync pytest -q tests/test_ns3_experiment.py
```

结果：13 项失败，全部因 `ModuleNotFoundError: flow_probe.ns3_experiment`；失败时生产模块、Shell 脚本和命令入口均未实现，符合预期。

日志：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/matrix-runner-tests-20260721/red-target.log`

### 绿测与回归

| 门禁        | 结果         | 日志或状态                                                                |
| ----------- | ------------ | ------------------------------------------------------------------------- |
| 目标测试    | 13/13 通过   | `runs/ns3-data/matrix-runner-tests-20260721/green-target-post-format.log` |
| 完整 pytest | 219/219 通过 | `runs/ns3-data/matrix-runner-tests-20260721/green-full-post-format.log`   |
| Shell 语法  | 状态 0       | `bash -n scripts/run_ns3_queue_truth_matrix.sh`                           |
| ns-3 编译   | 状态 0       | `env USER=ns3builder ./ns3 build scratch/flow-probe-queue-truth`          |

Black 格式化改变两个 Python 文件后，主代理已使用 rsync 重新同步；本地与服务器对应 Python 文件的 SHA-256 完全一致。格式化后的服务器目标测试 13/13、完整回归 219/219 再次通过。

## 在线冒烟

- 服务端目录：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/matrix-runner-smoke-20260721-v1`
- 本地目录：`/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/ns3-data/matrix-runner-smoke-20260721-v1`
- 场景：两个不同机制场景、随机种子 42。
- SwanLab 项目：`mortiswang/malicious-traffic-llm`。
- SwanLab 运行编号：`0qcukux8`。
- 运行地址：`https://swanlab.cn/@mortiswang/malicious-traffic-llm/runs/0qcukux8/chart`。
- 状态：运行器、逐组日志、CSV 验证、哈希、本地数值指标和在线完成状态均已通过。

## 正式矩阵

### 运行索引

- 服务端目录：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/ns3-queue-truth-formal-20260721-v1`
- 本地目录：`/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/ns3-data/ns3-queue-truth-formal-20260721-v1`
- 本地归档状态：rsync 完整归档后只读核对通过。
- SwanLab 项目：`mortiswang/malicious-traffic-llm`。
- SwanLab 运行编号：`qd8cw9ap`。
- 运行地址：`https://swanlab.cn/@mortiswang/malicious-traffic-llm/runs/qd8cw9ap/chart`。

### 验证统计

| 指标                        |      结果 |
| --------------------------- | --------: |
| 成功组数                    |        21 |
| 失败组数                    |         0 |
| 唯一 `group_id`             |        21 |
| CSV 文件数                  |        21 |
| 每份 CSV 字段数             |        46 |
| 总窗口数                    |      2520 |
| 每类场景窗口数              |       360 |
| 过渡窗口数                  |         9 |
| L3 残差非零窗口数           |         0 |
| 包残差非零窗口数            |         0 |
| qdisc 丢弃 L3 字节          | 220324568 |
| 下游随机误码损失 PPP 帧字节 |    137020 |

七个场景均按固定顺序生成随机种子 42、43、44 的三个组。完整验证摘要确认每类场景各 360 个窗口，总计 2520 个窗口。

### 正式制品

- 配置快照：`config_snapshot.json`
- 环境快照：`environment_snapshot.json`
- 生成器源码哈希：`source_sha256.json`
- 21 份 CSV 哈希：`csv_sha256.json`
- 逐组状态：`group_status.json`
- 总运行状态：`run_status.json`
- v4 验证摘要：`validation_summary.json`
- 本地 SwanLab 指标：`swanlab_metrics.json`
- 总制品清单：`artifact_manifest.json`
- 控制台日志：`console.log`
- 逐组日志：`logs/`
- CSV：`csv/`
- SwanLab 原始日志：`swanlog/ns3-matrix/`

本地归档复核进一步确认：

- `artifact_manifest.json` 状态为 `finished`、运行编号为 `qd8cw9ap`，共登记 74 个制品路径。
- `csv_sha256.json` 包含 21 条记录和 21 个不同的 SHA-256。
- 本地逐文件执行 SHA-256 复算，21 份 CSV 全部与 `csv_sha256.json` 一致；逐行字段数检查全部为 46。
- `source_sha256.json` 与本地 `ns3/queue_truth_scenario.cc` 的 SHA-256 均为 `492840219fa7286506cd0bca445f602ffab437f430b791ff25c63f4e32853ff4`。
- `csv/` 包含 21 份 CSV，`logs/` 分别包含 21 份标准输出和 21 份标准错误日志。
- SwanLab 原始文件为 `swanlog/ns3-matrix/run-20260721_103505-qd8cw9ap/run-qd8cw9ap.swanlab`。
- `swanlab_metrics.json` 包含 22 个严格递增步骤，最终指标与 `validation_summary.json` 完全一致。

### SwanLab 验收

- 云端运行信息接口返回状态 `FINISHED`。
- 云端汇总接口返回 6 个数值标量键。
- 6 个标量键均具有最终 `step=22` 数据点，对应 21 个逐组步骤和 1 个最终汇总步骤。
- 图表页地址已经实际验收，不以本地上传完成提示替代云端检查。

## 失败与中断记录

1. 初次尝试由实现子代理上传红测文件时，本地权限审查拒绝向外部 GPU 服务器传输新文件。该次尝试没有修改服务器；主代理取得精确授权后完成上传和红测。本任务没有通过远端命令注入或其他方式绕过拒绝。
2. 红测的 13 项失败是生产模块尚不存在造成的预期失败，完整日志保留在唯一目录中。
3. 功能实现、目标测试、完整回归、Shell 语法、ns-3 编译、在线冒烟和正式矩阵没有其他失败记录。
4. 本报告首次执行 Prettier 写入时因命令沙箱把 `.Codex/` 对子进程设为只读而返回 `EPERM`。Unix 所有权和模式正常，普通项目文件可写而 `.Codex/docs/` 文件对 shell 均不可写，根因定位为路径沙箱策略；随后只对本报告的 Prettier 命令授予受控写权限，格式化成功并通过 `prettier --check`。

## 格式与静态检查

- Black：已格式化 `src/flow_probe/ns3_experiment.py` 和 `tests/test_ns3_experiment.py`，随后 `black --check` 通过。
- Ruff：上述两个 Python 文件执行 `ruff check --no-cache`，检查通过。
- Shell：`bash -n scripts/run_ns3_queue_truth_matrix.sh` 通过。
- Markdown：本报告最终内容补齐后集中执行 Prettier。
- Git：本报告最终内容补齐后对本任务文件执行 `git diff --check`。

## 遗留风险

- ns-3 正式矩阵只提供物理真值与受控机制证据，不能替代 GeNIS 和 DEDALE 的检测性能或跨域证据。
- `configured_capacity_integral_link_bytes` 只表示配置容量积分，可作为外生控制量或归一化尺度，不能解释为实际离队量。
- 保存的双零残差来自生成器恒等式，只能审计数据。后续 PINN 损失必须作用于模型预测的可微状态，不得读取这两个审计字段作为训练残差。
- 正式制品现已完成本地同路径归档；当前没有阻塞任务交付的工程问题。
