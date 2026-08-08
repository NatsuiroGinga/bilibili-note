# 任务十三：三目标梯度可行性诊断实现与正式报告

- **日期**：2026-07-21 至 2026-07-22
- **状态**：实现、2 批次在线冒烟与 20 批次正式诊断均完成
- **正式 20 批次诊断**：`cvq5h4hu`，`FINISHED`
- **SwanLab 项目**：`mortiswang/malicious-traffic-llm`
- **SwanLab 冒烟运行**：`oduih10o`，`FINISHED`

## 1. 实现范围

本任务实现不更新参数的生成、稀疏状态和物理三目标共享 LoRA 梯度可行性诊断。修改文件如下：

- 新建 `thesis/experiments/llm_probe/src/flow_probe/gradient_feasibility.py`。
- 修改 `thesis/experiments/llm_probe/src/flow_probe/gradient_conflict.py`。
- 新建 `thesis/experiments/llm_probe/tests/test_gradient_feasibility.py`。
- 修改 `thesis/experiments/llm_probe/tests/test_gradient_conflict.py`。
- 修改 `thesis/experiments/llm_probe/pyproject.toml`。

新增命令：

```text
flow-probe-diagnose-gradient-feasibility
```

实现内容：

1. 不可变 `DirectionSolution`，保存三目标权重、下降边际和目标值。
2. 三单位梯度 Gram 矩阵的形状、有限性、对称性、单位对角线和半正定校验。
3. 分辨率为 0.02 的确定性整数单纯形网格共同下降求解。
4. 生成边际不低于 0.95 的保护方向求解。
5. 独立生成验证梯度与状态、物理训练梯度之间的归一化 G5 反应代理。
6. GeNIS 训练、GeNIS 验证和 ns-3 物理三套独立确定性样本顺序。
7. `anchor0_only` 状态监督掩码；物理残差继续使用完整五锚点预测状态。
8. 十类强制制品、逐步 SwanLab 在线指标、`optimizer_updates=0` 和 LoRA 持久梯度检查。

`gradient_conflict.py` 只增加可选 `state_masks` 参数。未提供掩码时继续使用原密集状态均方误差，保持任务七行为；提供掩码时使用稀疏状态损失，物理梯度路径不变。

未修改配置、数据集、模型权重、论文正文或 `output/第一创新点实验总控.md`。

## 2. 本地门禁

- Black 完成，四个相关 Python 文件格式通过。
- Ruff 首次发现一个未使用类型导入；删除后检查通过。
- `python -m py_compile` 通过。
- `git diff --check` 通过。
- 按仓库规则未在本机运行 pytest。

## 3. 服务器同步与入口刷新

从本地项目根目录对以下五个文件分别执行白名单同步：

```text
expect /tmp/gpu-rsync-push.exp <本地绝对文件> <服务端同构绝对文件>
```

同步使用 `rsync -rtv --partial --progress`，未使用 `--delete`。五次返回状态均为 0。

服务器入口只执行：

```text
uv pip install --no-deps -e .
```

返回状态为 0。未执行裸 `uv sync` 或裸 `uv sync --locked`。

## 4. 服务器目标测试

目标测试命令：

```text
uv run --no-sync pytest tests/test_gradient_feasibility.py tests/test_gradient_conflict.py tests/test_physics_train.py -q
```

首次结果为 **39 通过、1 失败**。失败只涉及正交 Gram 的并列最优权重预期：求解器按固定的生成优先排序返回 `(0.36, 0.32, 0.32)`，测试错误假定另一同目标值解 `(0.34, 0.34, 0.32)`。最小修复只更正测试预期，没有修改求解器、数学目标或运行器。

最终结果为：

```text
40 passed in 1.50s
```

日志：

- 首次日志：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/physics-gradient-feasibility/verification-20260721-task13/target-tests.log`
- 最终日志：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/physics-gradient-feasibility/verification-20260721-task13/target-tests-rerun.log`

## 5. 两批次在线冒烟

启动前门禁：

- 输出目录不存在。
- GPU 无计算进程。
- `/root/autodl-tmp` 使用率 64%，可用 19 GiB。

运行命令：

```text
uv run --no-sync flow-probe-diagnose-gradient-feasibility \
  --config configs/physics_sparse_seed42.yaml \
  --output-dir runs/physics-gradient-feasibility/qwen3-1.7b-seed42-anchor0-smoke2-v1 \
  --run-name qwen3-1.7b-seed42-anchor0-smoke2-v1 \
  --model-path /root/autodl-tmp/thesis/models/Qwen3-1.7B \
  --paired-batches 2
```

- `screen`：`285104.task13-gf-smoke2`，运行结束后正常退出。
- 服务端输出：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/physics-gradient-feasibility/qwen3-1.7b-seed42-anchor0-smoke2-v1/`
- 本地归档：`thesis/experiments/llm_probe/runs/physics-gradient-feasibility/qwen3-1.7b-seed42-anchor0-smoke2-v1/`
- 外部日志：`runs/physics-gradient-feasibility/verification-20260721-task13/smoke-screen.log`
- SwanLab：`oduih10o`
- 运行地址：`https://swanlab.cn/@mortiswang/malicious-traffic-llm/runs/oduih10o/chart`

### 5.1 两批逐步指标

| 指标             |   第 1 批 |   第 2 批 |
| ---------------- | --------: | --------: |
| 训练生成损失     |  3.911332 |  3.082007 |
| 独立验证生成损失 |  3.460897 |  3.153750 |
| 稀疏状态损失     |  0.166002 |  0.167536 |
| 物理损失         |  0.068411 |  0.072070 |
| 严格共同下降     |         1 |         1 |
| 生成否决         |         1 |         1 |
| 双辅助有效参与   |         0 |         0 |
| G5 状态反应代理  |  0.016066 |  0.020350 |
| G5 物理反应代理  | -0.026112 | -0.020917 |
| 单批时间/秒      |  4.625522 |  3.660535 |
| 峰值显存/MiB     |  3412.315 |  3545.315 |

共同下降解：

| 批次 | 权重：生成/状态/物理 | 边际：生成/状态/物理           | 最小边际 |
| ---- | -------------------- | ------------------------------ | -------: |
| 1    | 0.38 / 0.30 / 0.32   | 0.377804 / 0.371920 / 0.371290 | 0.371290 |
| 2    | 0.38 / 0.30 / 0.32   | 0.377242 / 0.364280 / 0.365302 | 0.364280 |

生成保护解：

| 批次 | 权重：生成/状态/物理 | 边际：生成/状态/物理           | 辅助最小边际 |
| ---- | -------------------- | ------------------------------ | -----------: |
| 1    | 0.96 / 0.00 / 0.04   | 0.959014 / 0.026314 / 0.016325 |     0.016325 |
| 2    | 0.96 / 0.00 / 0.04   | 0.959040 / 0.023000 / 0.016965 |     0.016965 |

### 5.2 汇总

- 逐步指标：**2 行**。
- 严格共同下降率：**2/2，100%**。
- 生成否决率：**2/2，100%**。
- 生成保护解双辅助有效参与率：**0/2，0%**。
- G5 状态反应代理均值：**0.018208**，非零率 **2/2**。
- G5 物理反应代理均值：**-0.023514**，非零率 **2/2**。
- 运行时间：**16.914 秒**。
- 峰值显存：**3545.315 MiB**。
- 参数更新次数：**0**。
- LoRA 持久梯度数量：**0**。

哈希：

- 输入清单：`70e290d5c5df7e8d2abea93e3dcf8cf20b472d59ded3574d51c07e9dd9ca9578`
- 三路样本顺序：`4066e8ac6b0767632070939f60eea1fb624fdc0f232b5e711be145ebdbcd7868`
- 状态掩码：`9caf4bb21a8d8e9d78412970fc9318d7778110eb51ee1d3e21c47125c59c7374`

## 6. 制品与追踪验收

以下十类制品均存在且非空：

1. `config.snapshot.yaml`
2. `environment.json`
3. `input_sha256.json`
4. `sample_order.json`
5. `state_mask.json`
6. `step_metrics.jsonl`
7. `summary.json`
8. `console.log`
9. `swanlog/gradient-feasibility/`
10. `artifact_manifest.json`

SwanLab 云端只读接口确认：

- 运行状态为 `FINISHED`。
- 严格共同下降、生成否决、双辅助参与、G5 状态反应和 G5 物理反应五个关键指标均返回步骤 1、2 的数据点。
- 运行清单为 `finished/online`，项目与工作区正确。

运行结束后 `screen` 已退出，`nvidia-smi` 未发现残留计算进程。结果目录与验证日志通过不含 `--delete` 的 `rsync` 回收到本地，返回状态为 0。

## 7. 二十批次正式诊断

### 7.1 运行与制品

正式命令使用与冒烟相同的配置、模型和状态掩码，只把 `--paired-batches` 改为 20，并写入独立目录。第一次启动曾附带入口不支持的 `--simplex-resolution` 与 `--generation-floor` 参数，命令在模型和数据初始化前被拒绝，没有生成可用于分析的指标。两个值已经由程序固定为 0.02 和 0.95，删除多余参数后重新启动正式运行。

- 服务端目录：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/physics-gradient-feasibility/qwen3-1.7b-seed42-anchor0-real20-v1/`
- 本地目录：`thesis/experiments/llm_probe/runs/physics-gradient-feasibility/qwen3-1.7b-seed42-anchor0-real20-v1/`
- 本地外部日志：`thesis/experiments/llm_probe/runs/physics-gradient-feasibility/verification-20260721-task13/formal-screen.log`
- SwanLab：`cvq5h4hu`
- 运行地址：`https://swanlab.cn/@mortiswang/malicious-traffic-llm/runs/cvq5h4hu/chart`

运行结束后无残留 GPU 计算进程或 `screen` 会话。正式目录和外部日志分别通过白名单 `rsync` 回收，两次返回状态均为 0，未使用 `--delete`。正式目录包含 15 个文件、413,993 字节；外部日志为 37,380 字节。本地文件与服务端文件的 SHA-256 逐项一致。

### 7.2 正式结果

| 指标                     |                        结果 |
| ------------------------ | --------------------------: |
| 严格共同下降             |               20/20，`100%` |
| 无保护方向触发生成否决   |               20/20，`100%` |
| 生成保护解双辅助有效参与 | 3/20，`15%`，步骤 6、10、16 |
| G5 状态反应代理均值      |      `0.008432`，非零 20/20 |
| G5 物理反应代理均值      |     `-0.020834`，非零 20/20 |
| 总运行时间               |                   83.264 秒 |
| 平均单批时间             |                    3.731 秒 |
| 峰值显存                 |                3545.315 MiB |
| 优化器更新               |                           0 |
| LoRA 持久梯度            |                           0 |

无保护共同方向的平均权重为生成、状态、物理 `0.361/0.311/0.328`，对应平均下降边际为 `0.355974/0.344955/0.348173`。这说明三目标在全部 20 个批次上都存在严格共同下降方向，但该方向在全部批次上都没有达到归一化生成边际 0.95。

加入生成保护后，平均权重变为生成、状态、物理 `0.960/0.005/0.035`，对应平均边际为 `0.959164/0.017407/0.012804`。只有步骤 6、10、16 同时给两个辅助目标非零权重并保持两者正下降边际；步骤 9 和 14 虽然也分配了状态权重，但物理边际为负，因此不计为双辅助有效参与。

三组梯度余弦分布如下：

| 梯度对     |      均值 |    最小值 |    最大值 |
| ---------- | --------: | --------: | --------: |
| 生成与状态 |  0.007908 | -0.015739 |  0.024245 |
| 生成与物理 | -0.022281 | -0.034729 | -0.014199 |
| 状态与物理 |  0.100238 | -0.205701 |  0.213870 |

生成与物理的 20 个余弦全部为负，再次确认冲突具有持续性，而不是少数异常批次造成。状态与物理的关系随批次变化较大，解释了生成硬保护下两个辅助目标难以稳定同时参与。

### 7.3 SwanLab 与归档验收

- SwanLab 云端状态为 `FINISHED`。
- 严格共同下降、生成否决、双辅助参与、G5 状态反应和 G5 物理反应五项指标均返回完整 20 个点。
- 云端均值与本地 `summary.json` 一致。
- `step_metrics.jsonl` 为 20 行。
- `artifact_manifest.json` 登记的 10 类制品齐全，包括配置快照、环境、输入散列、样本顺序、状态掩码、逐步指标、汇总、控制台日志、清单和 SwanLab 日志目录。

### 7.4 研究裁决

1. **共同下降方向存在不是主要障碍**：对称或非对称共同下降求解在局部几何上可行。
2. **生成目标保护必须显式进入算法**：不受保护的最大最小共同方向在 20/20 批次触发生成否决，G2 和 G3 后续必须报告这一失效率，不能只报告辅助目标改善。
3. **固定硬保护会压缩辅助目标空间**：在当前 0.95 生成边际下，双辅助有效参与率只有 15%。G4 需要按物理可靠性动态选择辅助目标，而不是强迫三目标每批都同时参与。
4. **G5 局部响应路径未退化**：两类代理 20/20 非零，足以允许进入训练比较，但它们不是完整超梯度，也不证明 G5 会带来最终检测或状态重建收益。
5. **下一步进入任务十四**：在同一随机种子、样本顺序、掩码和有效更新次数下比较 G0 至 G5；只有训练结果通过生成恶化不超过 5%、未观测状态误差和物理残差均改善至少 10% 的门槛，才能冻结正式协调算法。

## 8. 风险与未完成项

1. 正式诊断只覆盖随机种子 42 的 20 个批次，用于选择训练机制，不作为三随机种子最终统计证据。
2. 0.95 是当前预注册的一阶生成保护线，任务十四仍需用实际生成损失和生成式检测指标验证它是否足够。
3. G5 反应代理只是归一化一阶点积，不是完整双层超梯度或训练收益证明。
4. 本任务不更新模型参数，因此不能单独裁决 G2 至 G5 的优劣，也不能冻结算法名称。
5. 独立审查按用户要求在正式运行期间停止；正式指标已经通过原始制品、云端数据和跨端散列三重核验，但代码独立复审未完成。
