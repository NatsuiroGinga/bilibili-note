# R2 物理旁路增量信号实现报告

## 结论

R2 物理旁路信号实验的代码合同已经实现，当前状态为 `implemented / prerequisites_pending`。本轮没有读取最终测试集，没有运行模型实验，没有生成性能结论，也没有修改样本、基线预算或冻结数据。

截至本报告落盘时，R2 数据尚未正式发布，`ns-3` 第二次正式矩阵的首配对仍失败，因此物理真值门禁为 `NO-GO`。三份配置保持 `status: prerequisites_pending`，所有输入摘要保持 `PENDING`；正式包装器会在创建运行目录前零写入停止。

## 已实现内容

### 输入合同与隔离门禁

- 正式分类入口只允许 `train-fit` 与 `validation`。
- 状态估计器就绪回执必须证明物理拟合只读取 `train-fit` 与 `calibration`，并明确记录 `forbidden_splits_read=false`。
- 所有数据、旁路、就绪回执和划分清单都必须绑定小写 SHA-256。
- 旁路 Parquet 必须精确覆盖开发训练和开发验证样本；含额外样本时失败，防止 `test`、`unseen-configuration` 或 `open-protocol` 被提前物化。
- 训练清单与开发验证清单不得重叠。多个开发困难切片允许合法重叠，但都必须声明 `split_id=validation`。
- 共同输入固定为 R2 的 8 个数值字段及其 8 个缺失掩码。
- 物理旁路固定为 5 个队列状态估计、4 个归一化残差、5 个不确定性、3 个专家适用掩码和 1 个协议置信度，共 18 维。

### 四组确定性对照

- `A`：只读取共同字段。
- `A+P`：追加真实物理旁路。
- `A+P_shuffle`：在同一数据源、传输族和划分内部置换完整旁路向量，不读取攻击标签。
- `A+P_random`：训练集在同数据源、同传输族内逐列独立置换，精确保留各维训练边际；验证集每一维只从对应训练池抽样，不使用验证集估计边际分布。
- 四组直接复用 `tabular_baselines._build_model("hgb")`，保持树数、叶节点、学习率、线程、类别权重和随机种子相同。
- 每个变体写出训练和开发验证特征矩阵 SHA-256，防止旁路生成漂移。

### 指标与统计

- 每个开发验证分区报告宏平均 F1、平衡准确率、良性误报率、Brier 分数和期望校准误差。
- 每个种子分别计算 `A+P`、置换旁路和随机旁路相对 `A` 的样本级配对自助置信区间。
- 另外直接计算 `A+P` 相对 `A+P_shuffle` 和 `A+P_random` 的配对置信区间，不能只通过两者相对 `A` 的差值间接推断。
- 三种子汇总固定读取 42、43、44，不允许缺失、替换或挑选种子；汇总报告逐种子正收益、置信区间下界及真实旁路是否同时优于两个控制组。
- 状态误差和物理残差来自状态估计器的 `calibration` 就绪回执，不能由公开数据隐藏状态猜测。

### 正式运行与跟踪

- 包装器按种子 42、43、44 顺序生成独立运行目录。
- 每个正式种子在线写入 SwanLab 项目 `mortiswang/malicious-traffic-llm`。
- 每个种子保存配置快照、输入合同、环境、预测、指标、SwanLab 标量和制品清单。
- 包装器保存启动日志、状态、退出码、能力清单和代码/配置绑定。
- 每个种子在 Python 与 `tee` 结束、最终状态和退出码落盘后调用收口接口，重新计算并登记启动证据哈希，避免把运行中的日志或状态摘要写入最终制品清单。
- 三个种子全部完成后才生成 `three_seed_summary.json`。

## 文件与 SHA-256

| 文件 | SHA-256 |
| --- | --- |
| `src/flow_probe/r2_physics_sidecar_signal.py` | `2a45813496de31a493d93f41483848db72647f994a33b0ed3c265189652f7b3f` |
| `configs/r2_physics_sidecar_signal_seed42.yaml` | `61e5d2e764f031a84dd9fa8183a3528cae5a3ee6348da0b1b6cd8801ff39231a` |
| `configs/r2_physics_sidecar_signal_seed43.yaml` | `5d0351c75f0fce91146eb597a25844f6ac2e84f0174a7ef1641a91c2b88b2516` |
| `configs/r2_physics_sidecar_signal_seed44.yaml` | `eb29dbafd346ea4103057e178448deffa6fe928621984bca8a06619e196a1f35` |
| `configs/r2_physics_sidecar_readiness_v1.example.json` | `2fd9beca97fa9ced14f3b252030db01c6fb7c5cd8286d3272717567184c10b6a` |
| `scripts/run_r2_physics_sidecar_signal.sh` | `3ab6e17e268e565a158ab93bdc650d31414f5b8b07edea79f45963c542919be5` |
| `.Codex/docs/sdd/task-r2-physics-sidecar-signal/task_plan.md` | `f929582c235ccd3ec00e179423d712129e52206af8f334f6d264d9b6c820c31b` |

## 验证记录

通过：

```text
python3 -m py_compile thesis/experiments/llm_probe/src/flow_probe/r2_physics_sidecar_signal.py
bash -n thesis/experiments/llm_probe/scripts/run_r2_physics_sidecar_signal.sh
```

通过：使用系统 Python 的 `yaml.safe_load` 和 `json.loads` 读取三份种子配置及就绪回执模板，并确认种子精确为 42、43、44，状态均为 `prerequisites_pending`，旁路摘要均为 `PENDING`。

首次组合验证在真实模块导入阶段停止，错误为系统 Python 缺少项目依赖 `pandas`。此前同一命令中的 `py_compile` 已通过；该错误属于解释器环境，不是源文件语法错误。没有安装依赖或修改代码绕过问题。项目 `uv` 可执行文件存在，但本机沙箱对默认缓存目录无写权限，因此本轮没有重复模块导入。

按任务约束未执行：

- Black、Ruff、Prettier 或其他格式化；
- Pyright；
- 抽象语法树解析；
- pytest、独立冒烟或全量测试；
- 服务器同步、模型训练或 SwanLab 正式运行。

## 输出合同

单种子目录：

```text
runs/r2-physics-sidecar-signal/formal-v0/seed-<seed>/
├── launcher.log
├── launcher-state.json
├── launcher-exit-code.txt
├── launcher-capabilities.txt
├── launcher-binding.txt
├── console.log
├── config_snapshot.json
├── input_contract.json
├── environment.json
├── predictions.jsonl
├── results.json
├── swanlab_metrics.json
├── swanlog/
└── artifact_manifest.json
```

三种子汇总：

```text
runs/r2-physics-sidecar-signal/formal-v0/three_seed_summary.json
```

## 未解除依赖

1. R2 发布根、`freeze-manifest.json`、四个视图和开发划分尚未正式发布。
2. `ns-3` TCP/普通 UDP 正式配对矩阵尚未通过守恒与状态真值门禁。
3. 基于 `train-fit` 拟合、只用 `calibration` 冻结尺度与不确定性的状态估计器尚未发布。
4. 公开数据开发旁路 Parquet 和就绪回执尚未生成。
5. 上述制品发布后，必须逐文件回填三份配置的真实 SHA-256，再把状态统一改为 `ready`；不得只修改状态跳过摘要。

## 遗留风险

- 本模块依赖后续 R2 任务 07/12 实际发布的列名和划分清单合同。若正式发布模式与计划不同，应修改本旁路消费者并重新审查，禁止放宽为任意列或任意分区。
- 同源同协议层只有一个样本时，置换旁路无法改变该样本；正式结果必须报告这类单元素层数量，不能把它们当作有效负对照。
- HGB 的树结构会因输入维度不同而产生不同实际节点。置换和随机旁路用于控制新增维度解释，但不能声称 `A` 与 `A+P` 的实际参数节点逐个相等。
- 当前仅完成实现，不构成 R2 有效、无效或能够提升公开数据检测性能的证据。
