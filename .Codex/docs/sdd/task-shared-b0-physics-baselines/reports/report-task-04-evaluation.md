# 任务 04：公开检测与训练拟合物理诊断薄封装实施报告

## 当前结论

- 状态：`implementation_complete_local`、`server_acceptance_pending`、`review_pending`。
- 七个白名单文件已经全部落盘。
- 真实模块导入与四份配置加载通过。
- 精确范围 `Pyright` 通过，结果为 `0 errors, 0 warnings, 0 informations`。
- 未运行 AST、Prettier、任何格式化工具或本机 `pytest`。

## 修改文件

- `thesis/experiments/llm_probe/configs/shared_b0_state_supervision_seed42_genis_batch16_v1.yaml`
- `thesis/experiments/llm_probe/configs/shared_b0_state_supervision_seed42_tqhc2_batch16_v1.yaml`
- `thesis/experiments/llm_probe/configs/shared_b0_standard_pinn_seed42_genis_batch16_v1.yaml`
- `thesis/experiments/llm_probe/configs/shared_b0_standard_pinn_seed42_tqhc2_batch16_v1.yaml`
- `thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_evaluation.py`
- `thesis/experiments/llm_probe/tests/test_shared_b0_physics_evaluation.py`
- `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/report-task-04-evaluation.md`

未修改 `evaluate_model.py`、任务 03 训练器、冻结数据、历史运行目录或公共物理公式。

## 固定配置

四份配置覆盖两条基线与两个公开清单的笛卡尔积：

- `state_supervision × GeNIS`
- `state_supervision × TQH-C2`
- `standard_pinn × GeNIS`
- `standard_pinn × TQH-C2`

每份配置固定：

- 服务器本地 `Qwen3-1.7B`、共同字段视图、种子 42、输入上限 512、生成上限 16。
- 对应任务 03 正式训练目录和独立公开评估输出目录。
- 批量 16、关闭长度分桶、`SDPA`、每批落盘、允许恢复。
- GeNIS 或 TQH-C2 既有冻结 JSONL，不创建新清单或改变记录。
- 训练拟合物理旁路、2421 条训练记录和每条基线唯一的 `physics_train_fit_diagnostic.json`。
- `status=review_pending` 与在线 SwanLab 元数据。

## 公开检测薄封装

`run_public_detection_evaluation` 不实现新的生成或解析逻辑。它在模型加载前完成训练和数据哈希预检，然后把原 `ProbeConfig`、`EvaluationSettings`、测试文件、适配器目录和跟踪配置原样传给 `evaluate_model.evaluate_model`。

薄封装补充并冻结：

- 基线身份与任务 03 完整训练绑定哈希。
- `training_binding.json` 和 `artifact_manifest.json` 文件哈希。
- LoRA 适配器目录树哈希。
- 状态头文件与元数据哈希。
- 分类训练、分类验证、物理旁路和旁路清单哈希。
- 公开评估文件哈希、样本顺序、标签合同和原公共评估绑定哈希。
- 当前薄封装代码哈希。

训练制品预检要求运行状态和训练摘要均为完成状态、优化步为 200、生成位置为 800、物理记录为 2421、非有限数为 0。关键适配器和状态头文件必须与任务 03 制品清单中的字节数及 SHA-256 一致。

公共评估仍由既有评估器负责聊天模板、标签合同、确定性贪心解码、批量生成、预测解析、批级日志和恢复。薄封装不会重写提示词、标签或解码参数。

完成结果存在时，薄封装先复核全部绑定和完成制品，再幂等返回，不重新加载模型。未完成运行保留相同绑定并继续调用原评估器的恢复路径。

## 训练拟合物理诊断

`run_physics_fit_diagnostic` 只接受：

```text
evaluation_scope=train_fit_diagnostic
```

它按 `sample_id` 连接普通分类记录与独立物理旁路，按 `stable_order` 冻结顺序，以 16 条为一批写入部分预测和进度。中断后只从最后完整提交的样本继续；完成结果存在且绑定一致时幂等返回。

诊断直接加载任务 03 的 LoRA 适配器与状态头，并复用任务 03 的普通状态提示词、最后有效令牌选择、旁路张量构造及现有 `queue_balance_residual`。没有复制队列平衡公式。

最终报告包含：

- 全五锚点状态均方误差和平均绝对误差。
- 有效监督元素上的状态均方误差和平均绝对误差。
- 五个锚点各自的均方误差、平均绝对误差和元素数。
- 掩码覆盖率、有效元素数与总状态元素数。
- 队列平衡残差均方误差和残差元素数。
- 非有限元素数。
- 按 `group_id` 的同口径汇总。

输出递归检查并拒绝“未见物理测试”“外部物理泛化”“跨拓扑泛化”“对新拓扑有效”和“对未见配置有效”等表述。该诊断不能作为外部物理或跨拓扑结论。

## 任务 05 最小接口

模块已提供：

- `load_shared_b0_physics_evaluation_config`
- `validate_training_artifacts`
- `preflight_evaluation`
- `run_public_detection_evaluation`
- `run_physics_fit_diagnostic`
- 命令行参数 `--config`、`--mode public_detection|physics_fit`、`--preflight-only`

任务 05 只需注册入口并按基线和 `genis|tqhc2|physics_fit` 选择对应配置与模式，无需修改本模块接口。

## 专项测试

专项文件包含 12 个测试函数，并通过参数化覆盖四份真实配置和五类禁止表述。测试覆盖：

1. 四份真实配置的基线、清单、批量、SDPA、恢复和诊断范围。
2. 非 SDPA 或非训练拟合范围立即失败。
3. 适配器、状态头、训练绑定、制品清单和数据哈希验证。
4. 状态头篡改立即失败。
5. 公共薄封装绑定的全部必需哈希。
6. 调用既有评估器时公共提示、生成上限和运行参数不变。
7. 已完成公共评估不再调用模型。
8. 未完成公共评估保留绑定并恢复。
9. 状态、掩码、残差和逐组指标与手算结果一致。
10. 训练拟合诊断拒绝外推表述。
11. 物理诊断从完整批次恢复，完成后幂等。
12. 同一基线的物理诊断绑定不依赖 GeNIS/TQH-C2 配置选择。

## 本地验证

### 真实导入与配置加载

结果：

```text
IMPORT_CONFIG_OK 4 [('standard_pinn', 'genis'), ('standard_pinn', 'tqhc2'), ('state_supervision', 'genis'), ('state_supervision', 'tqhc2')]
```

### Pyright

命令：

```bash
.venv/bin/pyright --project /private/tmp/shared-b0-evaluation-pyright.json
```

结果：

```text
0 errors, 0 warnings, 0 informations
```

### 无模型纯行为核验

使用临时训练制品和注入评估器验证公共路径，结果：

```text
PURE_BEHAVIOR_OK completed True 1 0.1 train_fit_diagnostic 64
```

这表示首次公共评估完成、再次调用幂等返回、既有评估器只调用一次、手算状态均方误差为 0.1、诊断范围正确且适配器树哈希为 64 位。

使用三条临时旁路模拟批次中断与恢复，结果：

```text
PHYSICS_RESUME_OK 3 True 3
```

这表示三条诊断记录完整恢复，完成后幂等，部分日志记录数为 3。

## 服务器目标测试

同步后运行：

```bash
uv run --no-sync python -B -c \
  'import flow_probe.shared_b0_physics_evaluation as module; print(module.CONFIG_SCHEMA_VERSION)'
uv run --no-sync pytest -q tests/test_shared_b0_physics_evaluation.py
```

独立复审不阻塞服务器测试或后续冒烟。服务器专项测试通过后，任务 05 可立即注册命令入口并执行数据与制品预检。

## 遗留风险

- 本机未加载真实 Qwen、PEFT、状态头、BF16 或 CUDA；物理诊断真实前向仍需服务器冒烟确认。
- 本机未运行 `pytest`；专项测试通过状态只能由服务器目标命令确认。
- 当前物理数据全部来自训练拟合集，不能支持未见配置或跨拓扑结论。
- 本任务没有启动公开评估、物理诊断或任何正式 GPU 运行。
