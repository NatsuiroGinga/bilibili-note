# 任务 4：无泄漏四窗口物理序列构造报告

## 结论

- 无泄漏四窗口物理序列构造器、测试、Shell 包装脚本和命令入口已经实现。
- 服务器最终目标测试 **14/14**、完整回归 **233/233** 通过。
- 正式矩阵共形成 2,457 个四窗口候选，排除 36 个包含过渡窗口的候选，最终保留 2,421 个样本。
- 训练、验证、测试分别固定使用随机种子 42、43、44，各 807 个样本、7 个场景和 7 个完整 `group_id`，三个切分之间无组交叉。
- `v1` 因外层启动脚本覆盖模块生成并登记哈希的 `console.log` 而无效，不得作为正式制品。正式有效制品仅为 `v2`，其 8 个清单制品的 SHA-256 已全部复算通过。
- 本任务只完成物理真值序列的数据工程门禁，不证明 PINN 机制已经产生检测增益。下一阶段必须先通过候选公式门禁，再启动 M0、M1、M2。

## 修改范围

任务 4 的实现涉及以下文件：

- 新增 `thesis/experiments/llm_probe/src/flow_probe/ns3_sequences.py`。
- 新增 `thesis/experiments/llm_probe/tests/test_ns3_sequences.py`。
- 新增 `thesis/experiments/llm_probe/scripts/build_ns3_sequences.sh`。
- 修改 `thesis/experiments/llm_probe/pyproject.toml`，增加命令入口 `flow-probe-build-ns3-sequences = "flow_probe.ns3_sequences:main"`。

本次文档子任务仅新增本报告，并更新实验总控与子代理进度；未修改上述实验代码、任何运行数据或服务器文件。

## 接口与样本契约

- Python 接口：`build_ns3_sequences(csv_paths, output_dir, horizon=4)`。
- 命令入口：`flow-probe-build-ns3-sequences`。
- Shell 入口：`scripts/build_ns3_sequences.sh <ns-3 真值输入目录> <唯一序列输出目录>`。
- 序列长度固定为 4，不允许跨 `group_id`、跨不连续窗口，也不保留任何包含 `traffic_phase=transition` 的候选。
- 每个样本的模型可观测输入恰好包含 5 个字段，每个字段保留连续 4 个窗口。
- 每个样本的状态监督恰好包含 12 个字段，每个字段保留连续 4 个窗口。
- 队列状态和流量项按各自窗口的 `configured_capacity_integral_link_bytes` 归一化；配置容量积分只作归一化尺度，不解释为实际离队量。
- 场景、组号、标签、绝对时间和保存的零残差不得进入模型可观测输入。
- 构造器拒绝复用已有输出目录，并核对正式矩阵 `csv_sha256.json` 中的源 CSV 哈希。

## 测试驱动记录

### 有效红测

服务器项目：`/root/autodl-tmp/thesis/experiments/llm_probe`

命令：

```bash
uv run --no-sync pytest -q tests/test_ns3_sequences.py
```

有效功能红测结果为 **14 项失败**：生产模块 `flow_probe.ns3_sequences` 尚不存在，且 `flow-probe-build-ns3-sequences` 命令入口尚未登记，符合测试先行预期。

本地归档日志：

`/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/ns3-data/sequence-tests-20260721/red-target-functional.log`

更早一次红测在收集阶段因服务器 Python 3.10 没有内置 `tomllib` 而中断，未到达生产行为断言，因此不作为有效红测证据。对应日志为：

`/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/ns3-data/sequence-tests-20260721/red-target.log`

### 最终绿测与完整回归

| 门禁        |         结果 | 本地日志                                                                                    |
| ----------- | -----------: | ------------------------------------------------------------------------------------------- |
| 目标测试    |   14/14 通过 | `thesis/experiments/llm_probe/runs/ns3-data/sequence-tests-20260721/green-target-final.log` |
| 完整 pytest | 233/233 通过 | `thesis/experiments/llm_probe/runs/ns3-data/sequence-tests-20260721/green-full-final.log`   |

目标测试覆盖四窗口边界、五个状态锚点、字段角色、逐窗归一化、组级切分、过渡窗排除、索引和时间连续性、非正容量拒绝、源哈希追踪、制品哈希、输出目录不可复用、固定长度以及命令和 Shell 入口。

## 正式序列制品

### 输入与输出路径

- 正式输入矩阵服务器路径：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/ns3-queue-truth-formal-20260721-v1`。
- 正式 `v2` 服务器路径：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2`。
- 正式 `v2` 本地归档路径：`/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2`。
- `v2` 外层启动日志：`/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2.launcher.log`。

### 样本统计

| 切分 |   随机种子 | 场景数 | 完整组数 | 候选数 | 排除过渡候选 | 保留样本 |
| ---- | ---------: | -----: | -------: | -----: | -----------: | -------: |
| 训练 |         42 |      7 |        7 |    819 |           12 |      807 |
| 验证 |         43 |      7 |        7 |    819 |           12 |      807 |
| 测试 |         44 |      7 |        7 |    819 |           12 |      807 |
| 合计 | 42、43、44 |      7 |       21 |  2,457 |           36 |    2,421 |

每个完整 120 窗口组产生 117 个长度为 4 的候选。三个攻击场景中的过渡窗口分别影响 4 个重叠候选，因此每个切分排除 12 个候选；四个良性场景不含被排除候选。

### 清单与哈希

`artifact_manifest.json` 登记以下 8 个制品，逐文件 SHA-256 复算结果均一致：

1. `console.log`
2. `field_roles_snapshot.json`
3. `sample_statistics.json`
4. `source_csv_sha256.json`
5. `split_manifest.json`
6. `test.jsonl`
7. `train.jsonl`
8. `validation.jsonl`

正式 `v2` 的启动摘要为：2,457 个候选、36 个过渡候选被排除、21 个完整组、2,421 个有效样本，验证状态为 `passed`。

## `v1` 失败与 `v2` 裁决

- `v1` 中，模块完成写入后已将 `console.log` 纳入 `artifact_manifest.json` 并计算哈希。
- 外层启动脚本随后把自身标准输出重定向到同一个 `console.log`，覆盖了模块生成的文件。
- 复核结果只有 `console.log` 的实际 SHA-256 与清单不一致，其他清单制品一致。
- 因此 `v1` 只能保留为失败证据，不能用于训练、分析、论文统计或后续路径引用。
- `v2` 将外层日志独立保存为同级 `ns3-queue-sequences-h4-seed-split-20260721-v2.launcher.log`，不再覆盖制品目录内的 `console.log`；8 个清单制品哈希全部通过，因此裁决为唯一正式版本。

## 启动失败与 GPU 环境恢复

### 首次正式启动失败

首次正式启动使用 `uv run --no-sync` 时找不到新增控制台入口，失败信息为 `Failed to spawn: flow-probe-build-ns3-sequences`。根因是服务器环境中的项目元数据未刷新，不是序列算法或输入数据错误。

本地失败日志：

`/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/ns3-data/sequence-tests-20260721/formal-attempt-1-entry-missing.log`

### 依赖误移除与恢复

- 为刷新元数据曾执行裸 `uv sync --locked`，该命令把 `gpu` 可选组中的训练依赖视为多余依赖并移除。
- 随后使用 `uv sync --locked --extra gpu` 恢复完整 GPU 环境。
- 恢复后确认 `torch 2.13.0+cu130`、`transformers 4.57.6`、`swanlab 0.9.0` 可导入，CUDA 可用且设备为 RTX 5090。
- 环境恢复日志本地路径：`/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/environment/uv-gpu-restore-20260721`。
- `AGENTS.md` 已增加禁止裸 `uv sync` 和裸 `uv sync --locked` 的规则；仅刷新本地项目代码或命令入口时应使用 `uv pip install --no-deps -e .`，完整同步必须显式带 `--extra gpu` 并先预演。

## 格式与静态检查

- 服务器行为门禁：目标测试 14/14、完整回归 233/233 通过。
- 本次文档子任务未修改或重新格式化实验代码，也未重复运行 Python 静态检查。
- 本报告、实验总控和进度文件最终只使用 Prettier 格式化，并使用 `git diff --check` 检查空白错误。

## 遗留风险与下一门禁

- 四窗口序列只提供受控物理真值和状态监督，不能替代 GeNIS 或 DEDALE 的检测性能与跨域证据。
- 保存的双零残差仅用于数据审计。M2 必须由模型预测状态与受控观测重新构造可微残差，禁止把保存的零残差直接读入损失。
- M0、M1、M2 尚未产生实验结果。启动前必须在 PINN 公式证据台账中完成来源语义、变量可观测性、量纲、极端条件、数值残差以及对共享参数非零梯度的门禁。
- `v1` 不得被后续脚本或文档误引用；所有正式路径必须明确包含 `-v2`。
