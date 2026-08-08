# 共享 B0 任务 05 正式训练包装器实施报告

日期：2026-07-31

## 实施范围

根据主代理最新收缩合同，本任务只实现正式训练入口和包装器。未实现冒烟、恢复检查、物理旁路命令入口或评估入口，任务 04 不作为正式训练启动前置条件。

## 修改文件

- `thesis/experiments/llm_probe/pyproject.toml`
  - 注册 `flow-probe-train-shared-b0-physics`。
  - 删除完全重复的第二个 `[tool.pyright]` 表，使 `uv` 可以解析项目配置。
- `thesis/experiments/llm_probe/scripts/run_shared_b0_physics_baselines.sh`
  - 仅接受 `formal state_supervision|standard_pinn`。
  - 两条基线分别绑定固定且互斥的正式输出目录。
  - 建立唯一启动证据目录并使用固定 `screen` 名称防止重复运行。
  - 启动前验证数据、模型、训练代码、物理旁路、磁盘、CUDA、BF16、训练协议和 SwanLab 在线配置。
  - 保存配置、代码、分类数据、物理数据和模型配置的 SHA-256 清单。
  - 使用 `PIPESTATUS` 分别保留训练命令与 `tee` 的退出状态；日志为空时补写诊断但不覆盖原始非零退出码。
  - 完成后核对 200 个优化步、400 个物理微步、800 个生成位置、2421 条物理记录、200 条步级指标、最终检查点、制品清单和本地 SwanLab 日志。
- `thesis/experiments/llm_probe/tests/test_run_shared_b0_physics_baselines_wrapper.py`
  - 覆盖参数白名单、两条固定输出、完成目录拒绝、受管启动、训练退出码、完成制品和 SwanLab 日志门禁。

## 验证结果

通过：

```text
bash -n scripts/run_shared_b0_physics_baselines.sh
退出码：0
```

```text
UV_CACHE_DIR=/tmp/uv-cache uv lock --check
结果：Resolved 124 packages in 23ms
退出码：0
```

```text
UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync pyright tests/test_run_shared_b0_physics_baselines_wrapper.py
结果：0 errors, 0 warnings, 0 informations
退出码：0
```

未通过但已定位为本机环境限制：

```text
uv run --no-sync python -c 'import flow_probe.shared_b0_physics_train'
结果：ModuleNotFoundError: No module named 'torch'
```

本机环境没有安装 `gpu` 可选依赖。按照实验规则未在本机安装训练依赖，也未运行本机 `pytest`；真实导入与包装器目标测试必须在服务器既有 `uv` GPU 环境执行。

另一次 TOML 验证最初使用 Python 3.10 不提供的 `tomllib`，返回 `ModuleNotFoundError`。随后改用 `uv lock --check`，项目配置解析通过，未增加无关依赖。

未执行任何格式化、抽象语法树解析或本机 `pytest`。

## 服务器验收命令

三个白名单文件已通过 `guarded_rsync.py` 单文件同步，应用收据如下：

| 文件 | SHA-256 | 应用收据 | 状态 |
|---|---|---|---|
| `pyproject.toml` | `476f80773ffc0a737f51d3453ad32c0ef384d382a2132a5bc1d844f4ff8b7bfe` | `runs/hook-receipts/shared-b0-task05-pyproject-apply-v1.json` | `finished` |
| `scripts/run_shared_b0_physics_baselines.sh` | `3a3bbd503439ccc533a08d5f1f471471f1864335e33fbfb4148e64f9d37049c8` | `runs/hook-receipts/shared-b0-task05-wrapper-apply-v1.json` | `finished` |
| `tests/test_run_shared_b0_physics_baselines_wrapper.py` | `f35a5a185c3ea47dfdb66ac10f07b958ac13853a0844fb0bfe1cea02ff1a6d97` | `runs/hook-receipts/shared-b0-task05-test-apply-v1.json` | `finished` |

三份应用收据均记录：

```text
applied=true
prepare_exit_code=0
transfer_exit_code=0
verify_exit_code=0
```

服务器入口安装命令：

```text
uv pip install --no-deps -e .
退出码：0
结果：flow-probe==0.1.0 可编辑安装成功
```

安装过程出现“无法硬链接，回退完整复制”的性能警告，不影响入口安装正确性，也没有触发依赖变更。

主代理随后根据用户最新指令取消独立目标测试，要求把必要运行时断言融合进正式实验。服务器 `pytest` 尚未启动，因此本任务没有启动或停止任何测试进程，也没有额外执行真实导入、Pyright、Shell 语法检查、格式化、抽象语法树解析、冒烟或训练。

## 遗留风险

当前 `shared_b0_physics_train.py` 虽然提供步级 `metric_logger` 接口，但命令行入口尚未构造 SwanLab 记录器。包装器已经强制检查在线项目、工作区、动态短标签和最终本地 `swanlog`，但训练端未接线前，正式运行即使完成训练也会在最终 SwanLab 制品门禁失败。该缺口必须由任务 03 在训练模块范围内补齐，不能由 Shell 包装器伪造指标。

## 当前状态

```text
implementation=completed
local_shell_syntax=passed
local_pyright=passed
pyproject_parse=passed
server_pytest=cancelled_by_latest_contract
server_editable_install=passed
server_real_import=not_run_by_latest_contract
swanlab_training_logger=blocked_by_task03
ready_for_server_sync=true
ready_for_formal_training=false
```
