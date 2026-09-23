# MPS 迁移分段诊断实施报告

## 结论

已新增独立诊断工具。工具只记录 DRIFT 官方双分支 Transformer 在本机 MPS 的启动资源与分段时长，不产生训练效果、方法效果或论文结论。

真实 MPS 诊断尚未由本实现代理启动；按实施计划由主代理在静态验收后运行。因而本报告没有把任何启动耗时或资源数字写成已观测事实。

## 实现范围

- 输入参数仅为 `--run-dir` 与 `--batch-size`。
- `--run-dir` 通过既有 `resolve_run_dir` 限制在 `thesis/experiments/llm_probe/runs` 下，拒绝绝对路径和越界路径。
- 启动器预存的运行目录只允许包含一个名为 `console.log` 的普通文件；其内容保留，不删除、不截断。其他文件、目录、符号链接和 `.partial` 文件均拒绝。
- `--batch-size` 固定为 `128`；真实批从 T17 良性／DGA 训练 Parquet 各读取 `64` 条，域名仅在进程内参与既有字符与子词编码。
- 分段顺序严格为 `construct_model`、`load_state_dict_file`、`apply_state_dict`、`move_model_to_mps`、`load_real_batch`、`first_forward`、`first_backward`。
- 权重通过 `torch.load(..., map_location="cpu", weights_only=True)` 读取，并以 `load_state_dict(strict=True)` 应用；不创建优化器、不执行优化器步骤、不写模型或数据副本。
- MPS 阶段结束调用 `torch.mps.synchronize()`，以等待实际 Metal 工作完成。PyTorch 2.12 官方接口已由主代理用 Context7 核验为无参数签名 `torch.mps.synchronize()`（签名 `()`）。
- 每阶段先原子写入 `phase-status.json` 的 `running` 状态，再执行耗时操作；终止时最后的 `running` 阶段保留为卡点。`timing.json` 保存单调时钟区间，`resource.jsonl` 保存 RSS 最大值、磁盘可用字节、设备和 PyTorch 版本。
- 输出不写域名、成员清单、攻击明文、Parquet 副本、Tokenizer 副本、权重或缓存。
- `metadata.json` 的输入和输出路径均写为相对仓库根目录的稳定路径，不写个人绝对路径。

## 资源证据与方法效果的边界

`phase-status.json`、`timing.json`、`resource.jsonl`、控制台阶段记录和输入／模型哈希只属于**启动资源证据**。它们可用于定位构造、权重加载、状态写入、MPS 迁移、首个前向或首个反向的耗时与资源卡点。本工具尤其用于定位 `first_forward`／`first_backward` 的资源与时长卡点，不是方法效果评估器。

本工具不计算准确率、误报率、鲁棒性、训练损失曲线或跨年份泛化，也不执行训练更新。因此工具输出不能作为**训练或方法效果证据**，不能否决 DRIFT 方法或改变论文子集合同。

## 文件与制品

输入路径复用现有官方入口：

- `runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2/model.py`
- `runs/models/drift-official-dsn2026/finetuning.pt`
- `runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2/artifacts/tokenizer/tokenizer-0-30522-both.json`
- `runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521/DRIFT_input_eSLD/T17_benign_train.parquet`
- `runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521/DRIFT_input_eSLD/T17_dga_train.parquet`

新增文件：

- `thesis/experiments/llm_probe/tools/ch3_drift_mps_startup_diagnostic.py`
- `.Codex/docs/2026-09-23-DRIFT源期训练抽样合同/mps-startup-diagnostic-report.md`
- `.Codex/docs/2026-09-23-DRIFT源期训练抽样合同/mps-startup-diagnostic-skill-receipt.json`

本任务未修改已有训练脚本、模型源码、配置、数据合同或其他代理文件。

## 静态验收

以下命令只做语法、帮助、导入隔离和既有入口静态检查；没有启动 MPS、读取 Parquet、加载权重或连接服务器。

| 检查 | 命令 | 退出码 |
| --- | --- | --- |
| Python 语法 | `/opt/miniconda3/envs/rwkv/bin/python -m py_compile thesis/experiments/llm_probe/tools/ch3_drift_mps_startup_diagnostic.py` | 0 |
| CLI 帮助 | `/opt/miniconda3/envs/rwkv/bin/python thesis/experiments/llm_probe/tools/ch3_drift_mps_startup_diagnostic.py --help` | 0 |
| 模块导入隔离 | `/opt/miniconda3/envs/rwkv/bin/python -c 'import sys; sys.path.insert(0, "thesis/experiments/llm_probe/tools"); import ch3_drift_mps_startup_diagnostic'` | 0 |
| 既有模型／编码入口静态导入 | `/opt/miniconda3/envs/rwkv/bin/python -c 'import sys; sys.path.insert(0, "thesis/experiments/llm_probe/tools"); import ch3_drift_official_checkpoint_t17_eval as m; assert all(hasattr(m, n) for n in ("encode_char", "encode_subword", "iter_domains"))'` | 0 |
| 差异检查 | `git diff --check -- thesis/experiments/llm_probe/tools/ch3_drift_mps_startup_diagnostic.py .Codex/docs/2026-09-23-DRIFT源期训练抽样合同/mps-startup-diagnostic-report.md .Codex/docs/2026-09-23-DRIFT源期训练抽样合同/mps-startup-diagnostic-skill-receipt.json` | 0 |

本轮未运行真实 MPS 诊断、训练或数据读取；真实诊断命令和阶段制品由主代理另行负责。本报告的静态验证不构成前向、反向或方法效果证据。

## 2026-09-23 主代理真实诊断结果

主代理以 `PYTORCH_ENABLE_MPS_FALLBACK=1` 在独立身份 `runs/diagnostics/ch3-drift-mps-startup-diagnostic-20260923-rerun2/` 完成真实 T17 开发批诊断。身份为 T17 两类训练文件各64条、总批128；没有优化器步骤、模型写出或方法效果指标。

| 阶段 | 墙钟秒 |
| --- | ---: |
| 模型构造 | 0.2652 |
| 权重读取 | 0.0454 |
| 严格状态写入 | 0.0127 |
| 迁移并同步 MPS | 0.3897 |
| 真实批读取与编码 | 0.3339 |
| 首前向 | 1.8692 |
| 首反向 | 1.4992 |

模型参数量为24,180,226；首前向 logits 为 `[128,2]`、位于 `mps:0`；首反向损失有限且位于 `mps:0`。虽然控制台记录了嵌套张量算子回退 CPU 的警告，但首前向和反向均完成，当前没有证据将其定性为稳定启动瓶颈，也不授权改变 `map_location="cpu"`、模型结构或批量。阶段收据显示诊断期间 MPS 缓存使可用磁盘短暂下降；资源结论只适用于该次开发批身份。

该制品关闭“模型迁移无法启动”的工程假设；下一项资源问题是论文专用子集下的递增规模稳态吞吐，而不是立即改写加载路径。
