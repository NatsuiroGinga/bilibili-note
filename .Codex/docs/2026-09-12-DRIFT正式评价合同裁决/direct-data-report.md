# 正式评价原 Parquet 直读接口报告

## 结论

直读适配已完成。三份配置和共享合同现已冻结为 `direct_parquet_read_only`；`assets` 门改为 `inputs`，`--materialize` 明确失败关闭。新模块提供源角色内存唯一化、目标固定哈希选择和独立精确唯一计数接口。

本机真实验证仅覆盖 `T17_benign_val` 与 `T17_dga_val` 两个验证文件，各 150000 行，身份为 `engineering_only`。全源 18 个源角色、T20–T25 目标面板、服务器容量、全量源重合和 family 资格仍未验证，不能据此宣称正式评价完成。

## 变更文件

仅变更简报限定的五个生产文件，以及本报告和技能收据：

1. `thesis/experiments/llm_probe/tools/ch3_drift_formal_contract.py`
2. `thesis/experiments/llm_probe/tools/ch3_drift_formal_data.py`
3. `thesis/experiments/llm_probe/configs/ch3-drift-formal-evaluation-v1.json`
4. `thesis/experiments/llm_probe/configs/ch3-drift-official-p2p3-formal-v3.json`
5. `thesis/experiments/llm_probe/configs/ch3-drift-bresnet-p2p3-formal-v1.json`

未修改 `ch3_drift_formal_edit.py`、两骨干训练脚本、远程启动器、恢复卡、原 Parquet、依赖锁和旧审计收据。未执行 Git 写操作、自动格式化、人工夹具、单元测试、训练、MPS/CUDA 或服务器连接。

## 合同修订

- 评价配置新增严格 `input_access`：模式为 `direct_parquet_read_only`，源顺序为 `input_role_order_then_row_first_occurrence`，去重键为 `exact_esld`，`derived_data_written=false`。
- 三份配置的 `allowed_modes` 删除 `materialize`；旧命令仍可解析，但合同以中文错误拒绝，不创建假完成状态。
- 合同门名称改为 `inputs`。三份配置保留原 30 角色、数据 revision、攻击档位、阈值和骨干训练数值。
- 两份训练配置的共享视图改为 `source_train_test_exact_unique_in_memory` 与 `source_val_exact_unique_in_memory`。

修订后规范配置 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| 评价配置 | `32eb1b32386ab1695bc37f03736b76bb97c11d0194883f07f52714469b4c35e9` |
| DRIFT 配置 | `c9e2d0f98f81aa5a1a7f1a9d08caff2797fde772aac0ca39fee67eaf028ccff2` |
| BResNet 配置 | `7ff35c79a2589b623ad05005942202498ccb2f16d27272705d83f68acdd9961c` |

代码 SHA-256：合同模块 `99665d44b76809b01f9ceadaaaab9f5a6549ad0fc4faa3f1cca8139a26717cd2`；直读模块 `bcddd8bb81bfdd8c6b064160086ed87ea40e4d990f40091d219f9f8b1aa98aad`。

## 公共接口

```text
audit_inputs(
    config: Mapping[str, Any],
    *,
    role_names: Sequence[str] | None = None,
    batch_size: int = 8192,
    config_sha256: str | None = None,
    audit_scope: str = "full",
) -> InputReceipt

load_source_unique_in_memory(
    role_group: str | Iterable[str],
    input_receipt: InputReceipt,
) -> SourceStore

iter_target_selected(
    year: int,
    class_name: str,
    input_receipt: InputReceipt,
) -> Iterator[EntityBatch]

count_target_unique_in_memory(
    year: int,
    class_name: str,
    input_receipt: InputReceipt,
) -> TargetUniqueCount
```

`InputReceipt` 记录请求角色的相对路径、字节数、Parquet 元数据行数、实读行数、行组数、字段类型、文件 SHA-256 和状态。`SourceStore` 按配置角色顺序及行首次出现顺序暴露 `entities`、`labels`、`sources`、`iter_batches()` 和聚合摘要；不提供序列化接口。`EntityBatch` 仅在消费进程内携带 exact eSLD、标签和成员摘要。目标选择器的 `selection_receipt` 在首次迭代完成时可读。

## 算法与安全边界

- PyArrow 仅在读取入口延迟导入；使用 `ParquetFile.iter_batches(columns=["domain", "label"], use_threads=False)`，原文件以只读方式打开。PyArrow 25.0.1 的接口依据 Apache Arrow 官方文档：[ParquetFile](https://arrow.apache.org/docs/python/generated/pyarrow.parquet.ParquetFile.html)。Context7 查询未返回 PyArrow 条目，未据此臆测接口。
- 每行严格要求非空字符串 `domain` 和与类别一致的整数标签 `0/1`；不 `strip`、不 `lower`、不重建 eSLD。空值、非法标签、字段变化、元数据／实读行数不一致直接失败。
- 源 Store 对合并角色执行 exact eSLD 首次出现唯一化。同标签重复计入聚合重复数；跨角色重复计入重合数；跨标签冲突计数后拒绝静默选择。
- 目标选择器按合同长度前缀成员哈希维护最大堆中的最小 200000 个完整摘要，堆满后使用单调下降的入选上界跳过淘汰大键；最终按摘要排序流式返回批次。超过上限时 `unique_count` 保持未知，不能用原始行数或堆大小代替。
- `count_target_unique_in_memory` 独立保存完整 exact eSLD 集合并返回精确唯一数、重复数和集合根；发生容量不足时返回 `blocked_no_non_materialized_exact_count`，不落盘替代。

## 真实 T17 CPU 审计

执行解释器固定为 `/opt/miniconda3/envs/rwkv/bin/python`。两次独立运行分别使用批大小 8192 和 16384：

- `runs/diagnostics/ch3-drift-formal-direct-read-development-v1/`
- `runs/diagnostics/ch3-drift-formal-direct-read-development-v1-batch16384/`

两文件均完整读取 150000 行；元数据与实读行数一致，字段均为 `domain,label`，文件 SHA-256 分别为 `b6e0ec6b16da3b7b3efe4c1fee4718807e3336ced458109d0cf05cd05d96f60d` 和 `dfd47b8e99837c0567b4da81595a55fe12aa0a452372694e552656454a14a0a4`。源 Store 聚合结果为原始 300000、唯一 300000、重复 0、跨角色重合 0、标签冲突 0。两类固定选择各 150000 个，精确唯一计数均为 150000；两批大小的 benign／dga 选择根和精确集合根完全一致。第一次开发审计峰值 RSS 收据为 187711488 字节。

收据只含路径、哈希、计数、根摘要、算法和未验证项，没有原始域名、成员清单、攻击字符串、数据库、缓存或 Parquet 副本。

技能收据已改用当前可读文件 `/Users/bilibili/.codex/skills/daily-coding/SKILL.md`，读取时间为 `2026-09-23T06:16:25Z`，SHA-256 为 `c550a289d2993a9d9c1e17fe2661cff3bc4022d8ed977a0bf8fea9e1ef485f01`。此前不可读的归档路径不再作为技能来源。

## 未覆盖项

本轮没有读取 T20–T25，也没有执行全源训练／验证角色、全量目标选择、服务器容量前检、源训练—验证交集政策或 family 资格审计。故 `engineering_only=true`、`target_full_scope_not_covered=true`，后续服务器入口必须重新生成完整输入和容量收据；不能把本轮 T17 结果升级为正式目标面板或方法效果结论。

## 验证命令

以下记录均为可直接执行的完整命令及实际退出码：

- `/opt/miniconda3/envs/rwkv/bin/python -m py_compile thesis/experiments/llm_probe/tools/ch3_drift_formal_contract.py thesis/experiments/llm_probe/tools/ch3_drift_formal_data.py`：`exit_code=0`。
- `/opt/miniconda3/envs/rwkv/bin/python -c 'import sys; sys.path.insert(0, "thesis/experiments/llm_probe/tools"); import ch3_drift_formal_contract, ch3_drift_formal_data; assert not any(name in sys.modules for name in ("torch", "numpy", "pyarrow"))'`：`exit_code=0`。
- `/opt/miniconda3/envs/rwkv/bin/python thesis/experiments/llm_probe/tools/ch3_drift_formal_contract.py --help && /opt/miniconda3/envs/rwkv/bin/python thesis/experiments/llm_probe/tools/ch3_drift_formal_data.py --help`：`exit_code=0`。
- `/opt/miniconda3/envs/rwkv/bin/python -c 'import sys; sys.path.insert(0, "thesis/experiments/llm_probe/tools"); from ch3_drift_formal_contract import load_config; [load_config(path) for path in ("configs/ch3-drift-formal-evaluation-v1.json", "configs/ch3-drift-official-p2p3-formal-v3.json", "configs/ch3-drift-bresnet-p2p3-formal-v1.json")]'`：`exit_code=0`。
- `/opt/miniconda3/envs/rwkv/bin/python thesis/experiments/llm_probe/tools/ch3_drift_formal_contract.py --gate inputs --config configs/ch3-drift-formal-evaluation-v1.json --run-dir runs/diagnostics/ch3-drift-formal-direct-read-development-v1 --audit`：`exit_code=0`。
- `/opt/miniconda3/envs/rwkv/bin/python thesis/experiments/llm_probe/tools/ch3_drift_formal_contract.py --gate inputs --config configs/ch3-drift-formal-evaluation-v1.json --run-dir runs/diagnostics/ch3-drift-formal-direct-read-materialize-reject --materialize`：`exit_code=2`，中文拒绝说明。
- `/opt/miniconda3/envs/rwkv/bin/python thesis/experiments/llm_probe/tools/ch3_drift_formal_data.py --config configs/ch3-drift-formal-evaluation-v1.json --run-dir runs/diagnostics/ch3-drift-formal-direct-read-development-v1 --audit --scope development --batch-size 8192`：`exit_code=0`。
- `/opt/miniconda3/envs/rwkv/bin/python thesis/experiments/llm_probe/tools/ch3_drift_formal_data.py --config configs/ch3-drift-formal-evaluation-v1.json --run-dir runs/diagnostics/ch3-drift-formal-direct-read-development-v1-batch16384 --audit --scope development --batch-size 16384`：`exit_code=0`。
