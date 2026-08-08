# 共享 B0 DistilBERT 服务器执行报告

日期：2026-07-30

## 当前状态

- 已完整读取仓库根、`thesis/`、`llm_probe/`、`scripts/` 与 `.Codex/docs/` 的适用规则，以及两份恢复文档、远程执行合同、实施计划和任务一报告。
- 已核对当前生产入口：命令行仅支持正式运行、`--preflight-only` 和 `--cpu-forward-smoke`；现有正式预检固定读取训练、GeNIS 与 TQH-C2 三份冻结输入，因此不能直接满足 16 条非最终训练冒烟的禁读 TQH-C2 合同。
- 已新增 `--gpu-smoke16-output DIR`：该分支只验证并读取候选训练与 GeNIS 开发文件，各确定性截取前 16 条，不加载 TQH-C2。
- 已新增独立冒烟运行配置：单轮、单优化步、独立不可复用输出目录，并保存有限损失、概率级增量预测、运行状态、本地 SwanLab 逐步指标、摘要和制品清单。
- 已新增 `scripts/run_shared_b0_distilbert_training.sh`，固定支持 `test|smoke|formal`；正式模式使用 `screen`，发现正式目录已存在即拒绝覆盖或复用。
- 三个执行文件已通过受管白名单 rsync 同步服务器并逐一核对 SHA-256。
- 服务器精确测试首次为 `10 passed, 1 failed`；唯一错误断言经一次最小修复后，原失败节点重跑为 `1 passed`。
- 16 条 GPU 冒烟已完成，正式种子 42 已在独立 `screen` 中启动。
- 本轮只允许新增独立 16 条冒烟路径与训练包装器；正式配置的 10,000/10,399/4,000 输入合同、正式输出目录和下载包装器保持不变。

## 计划内文件

- `thesis/experiments/llm_probe/src/flow_probe/shared_b0_distilbert_baseline.py`
- `thesis/experiments/llm_probe/tests/test_shared_b0_distilbert_baseline.py`
- `thesis/experiments/llm_probe/scripts/run_shared_b0_distilbert_training.sh`
- `.Codex/docs/sdd/task-shared-b0-distilbert-baseline/implementation-report.md`

## 验证记录

- 通过：本地 Python 不落盘语法编译，退出码 `0`。
- 通过：本地 `bash -n scripts/run_shared_b0_distilbert_training.sh`，退出码 `0`。
- 通过：本地 `git diff --check`，退出码 `0`。
- 通过：Black 集中格式化两份 Python 文件；生产模块已重排，测试文件无需修改。
- 已执行唯一一次 Ruff：仅报告原有导入排序 `I001` 与 `SIM105` 风格建议，没有语法或结构问题；按局部规则接受且不重复运行。
- 通过：服务器包装器 `bash -n`，退出码 `0`。
- 通过：服务器精确目标测试合计 `11` 个节点；首次 `10` 个通过，唯一 Brier 断言修复后精确节点 `1 passed in 0.43s`。
- 通过：服务器 16 条 GPU 冒烟，包装器退出码 `0`。
- 通过：服务器种子 42 正式 `screen` 启动门禁；会话保持运行。

## 同步记录

- 生产模块 SHA-256：`c3b25a3c03d09e3c346cc7cfacf9de8e1d5eea1bddaa3f46c5183c2d217a78c9`。
- 包装器 SHA-256：`fc8252c993d17c6e2934162eab29658b57fc08539640862534e84ad40b5580f4`。
- 测试文件首次 SHA-256：`564cad7ad83aedd7a8a62c5ad2aefef65d3870e2e2ed37897645993a5c09237d`。
- Brier 单断言修复后测试文件 SHA-256：`d4c1fd18d78ddf5de8f2a2fd631268438ab9eaa831d63d4b012a14ba1ebeff50`。
- 四份同步收据均为 `finished/applied=true`，远端 SHA-256 核对退出码均为 `0`。

## 运行制品

- 16 条冒烟：服务器 `runs/smoke/shared-b0-distilbert-smoke16-seed42-20260730T111935Z-30099/`。
- 冒烟状态：`finished`；训练与 GeNIS 开发各 `16` 条；优化步 `1`；增量预测 `16` 行；TQH-C2 为 `not_started/forbidden`；SwanLab 运行号 `y44asbke`，上传 `102` 条记录。
- 正式种子 42：服务器 `runs/baselines/shared-b0-distilbert-seed42-theory-selection-review-pending-v1/`。
- 正式 `screen`：`shared-b0-distilbert-seed42-v1`。
- 正式 SwanLab：在线项目 `mortiswang/malicious-traffic-llm`，运行号 `5dmehlxi`，标记为 `review_pending`。
- 正式完成状态：`finished`，全局步数 `939/939`，最佳轮次 `3`，最近检查点 `checkpoint-939`，TQH-C2 固定评价状态 `finished`，失败字段为空。

## 正式结果

- GeNIS 开发验证：`10,399` 条，宏平均 F1 `0.9768536999609979`，恶意召回率 `1.0`，良性误报率 `0.0743847874720358`，期望校准误差 `0.011115464577604494`，布里尔分数 `0.01226791095385432`。
- TQH-C2 固定外部验证：`4,000` 条，宏平均 F1 `0.8221599341706451`，恶意召回率 `0.9615384615384616`，良性误报率 `0.16698232323232323`，期望校准误差 `0.06921584195981266`，布里尔分数 `0.060898170211063196`。
- 两份预测分别为 `10,399` 行与 `4,000` 行。
- 训练耗时 `353.4499367251992` 秒，总耗时 `361.30275440588593` 秒；峰值 GPU 已分配内存 `2,783,500,800` 字节，峰值 GPU 保留内存 `2,944,401,408` 字节。
- 服务器对 `artifact_manifest.json` 登记的全部制品执行 `sha256sum -c --quiet`，退出码 `0`。

## SwanLab 云端验收

- 正式运行号：`5dmehlxi`。
- `run info` 返回 `state=FINISHED`，运行地址为 `https://swanlab.cn/@mortiswang/malicious-traffic-llm/runs/5dmehlxi/chart`。
- `run summary` 返回训练、三轮 GeNIS 开发与两份最终评价指标，数值与本地摘要一致。
- `run metrics` 已核对 `train/loss`、`dev/macro_f1`、`final/genis/macro_f1` 与 `final/tqhc2/macro_f1`；四个键均存在数据点。

## 本地回收

- 正式小型制品回收到本机 `thesis/experiments/llm_probe/runs/baselines/shared-b0-distilbert-seed42-theory-selection-review-pending-v1/`。
- 回收内容包括配置快照、运行状态、运行/输入/模型绑定、环境、控制台日志、开发历史、SwanLab 逐步指标、摘要、成本、两份指标、两份预测、最终检查点清单、最佳模型选择清单、制品清单和 `336 KiB` SwanLab 原始日志目录。
- 启动器证据回收到本机 `thesis/experiments/llm_probe/runs/launchers/shared-b0-distilbert-formal-20260730T112032Z-30533/`。
- 本机对制品清单覆盖的已回收 `23` 个文件逐一重算 SHA-256，全部一致。
- 本机状态门禁通过：`run_state=finished`、`current_step=939`、`tqhc2_evaluation_status=finished`、`failure=null`、SwanLab attempt 为 `finished`、启动器状态为 `finished`、启动器退出码为 `0`。

## 启动器状态修复

- 正式计算已完成且退出码为 `0`，但启动器 `status.txt` 一度错误保留为 `failed`。
- 根因：formal worker 只写 `exit-code.txt`，没有依据最终退出码回写 `status.txt`；启动阶段的短时会话检查结果因此可能永久覆盖真实完成状态。
- 一次最小修复：worker 退出前按退出码写入 `finished` 或 `failed`；本地与服务器 `bash -n` 均通过，受管同步后包装器 SHA-256 为 `f9755c23879b5dcae38919e2106e17a0a45f7119d9e83b63492ffebc8fc06cdd`。
- 本次状态依据 `run_state=finished`、启动器退出码 `0` 和日志完成摘要修复为 `finished`；没有重跑实验。

## shutdown_ready

- `shutdown_ready=true`。
- 最终检查点存在于 `/root/autodl-tmp/thesis/experiments/llm_probe/runs/baselines/shared-b0-distilbert-seed42-theory-selection-review-pending-v1/checkpoint-939/`。
- 服务器 `screen -ls` 无会话；GPU 计算进程为空；`pgrep` 未发现本任务训练模块、训练包装器或 rsync 进程。
- 关键小型制品与 SwanLab 原始日志已回收并通过本机哈希核对。
- 未执行关机；由主代理做最终只读复核后关机。

## 遗留风险

- 现有模块正式评价会无条件读取并评价 TQH-C2；冒烟必须使用独立执行路径，不能通过缩短正式配置来绕过。
- 当前工作树包含其他任务的未提交改动；本任务只触碰上述白名单文件，不回滚或覆盖其他改动。

## 故障记录

### 服务器精确测试首次运行

- 命令入口：`bash scripts/run_shared_b0_distilbert_training.sh test`。
- 结果：`10 passed, 1 failed`，退出码 `1`。
- 唯一失败：`test_binary_metrics_include_detection_calibration_and_brier_values`。
- 根因：测试输入的四项平方误差为 `0.01`、`0.36`、`0.04`、`0.36`，均值为 `0.1925`；既有断言误写为 `0.1425`，生产实现计算正确。
- 最小修复：只把该断言改为 `pytest.approx(0.1925)`；未修改生产指标实现或其他测试。
- 失败证据保留在本报告；修复后只重跑该精确节点，再继续 GPU 冒烟门禁。
