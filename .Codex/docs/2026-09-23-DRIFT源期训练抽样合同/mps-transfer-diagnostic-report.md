# DRIFT MPS 权重迁移阶段诊断报告

## 结论

本次实现只覆盖官方模型的四个启动阶段：`construct_model`、`load_state_dict_file`、`apply_state_dict` 和 `move_model_to_mps`。工具不读取 Parquet 或域名，不执行前向、反向、训练、优化，也不写模型、检查点或数据副本。

## 输入与输出

- 工具：`thesis/experiments/llm_probe/tools/ch3_drift_mps_transfer_diagnostic.py`
- 唯一参数：`--run-dir`；运行目录由既有 `resolve_run_dir` 限制在 `llm_probe/runs` 下。
- 官方模型引用：`runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2/model.py`。
- 官方检查点：`runs/models/drift-official-dsn2026/finetuning.pt`。
- 阶段收据：`phase-status.json`、`timing.json`、`resource.jsonl` 和 `metadata.json`。

每个阶段在开始前原子写入 `phase-status.json` 的 `running` 状态。每阶段的计时和资源记录包含耗时、RSS、可用磁盘、设备、工具代码摘要和检查点摘要。进程被外部中止时不会捕获 `KeyboardInterrupt` 或终止信号，最后一个阶段因此保留为 `running`。

## PyTorch 接口核验

已核验目标环境 PyTorch 版本为 2.12；`torch.mps.synchronize()` 的官方签名为无参数调用 `()`，用于在 `move_model_to_mps` 完成后等待 MPS 队列实际完成。该同步只在 MPS 可用且迁移阶段结束后调用。

## 验收边界

本轮只执行 `--help`、语法编译、隔离导入和差异检查，不运行真实 MPS 诊断。收据中的 `real_run.applicable=false`；真实运行由主代理在静态验收后负责，因此本报告不包含启动耗时或模型效果结论。

## 启动器兼容性修复

首次真实启动未进入 MPS：启动器预先创建了 `run-dir/console.log`，旧检查拒绝任意非空运行目录。现已修复为仅允许一个名为 `console.log` 的常规文件（保留其已有内容，不删除、不截断）；其他文件、目录、符号链接和 `.partial` 仍拒绝。修复后的启动命令为：

`/opt/miniconda3/envs/rwkv/bin/python thesis/experiments/llm_probe/tools/ch3_drift_mps_transfer_diagnostic.py --run-dir runs/diagnostics/<new-run-dir>`

本轮未重跑真实 MPS；失败原因和修复均属于启动前路径门禁，未产生阶段或模型证据。

实际执行的验证命令均以退出码 `0` 完成：

- `/opt/miniconda3/envs/rwkv/bin/python -m py_compile thesis/experiments/llm_probe/tools/ch3_drift_mps_transfer_diagnostic.py`
- `/opt/miniconda3/envs/rwkv/bin/python thesis/experiments/llm_probe/tools/ch3_drift_mps_transfer_diagnostic.py --help`
- `PYTHONDONTWRITEBYTECODE=1 /opt/miniconda3/envs/rwkv/bin/python -c 'import importlib.util; ...; print("isolated-import-ok")'`（隔离导入，不执行 `main`）
- `/opt/miniconda3/envs/rwkv/bin/python -c 'import inspect, torch; print(torch.__version__); print(inspect.signature(torch.mps.synchronize))'`，输出 `2.12.0` 和 `() -> None`。
