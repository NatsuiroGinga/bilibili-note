# R2 DistilBERT 物理旁路探针实施报告

## 结论

阶段二 DistilBERT 小型 Transformer 旁路探针的代码与三份种子配置已经实现，并完成独立复审提出的运行绑定、失败恢复和磁盘占用修复。入口固定使用 TQH-C2 开发训练 `2,048` 条、开发验证 `512` 条，按同一基础文本、样本、标签、模型结构、优化器和训练预算执行 `T-A`、`T-P`、`T-S`、`T-R` 四组。

本轮没有下载模型、启动 GPU、运行训练、连接 SwanLab 或生成实验结果。当前状态只能记为 `implemented / syntax_checked / runtime_review_pending`，不能记为实验完成或物理旁路有效。

## 已实现文件

- `thesis/experiments/llm_probe/src/flow_probe/r2_distilbert_sidecar_probe.py`
- `thesis/experiments/llm_probe/configs/r2_distilbert_sidecar_probe_seed42.yaml`
- `thesis/experiments/llm_probe/configs/r2_distilbert_sidecar_probe_seed43.yaml`
- `thesis/experiments/llm_probe/configs/r2_distilbert_sidecar_probe_seed44.yaml`
- `.Codex/docs/sdd/task-r2-physics-sidecar-signal/distilbert_probe_impl_report.md`

没有修改已有共享 B0 DistilBERT 基线、HGB 先导入口、先导输入、正式 R2 `prerequisites_pending` 配置或任何运行制品。

## 输入与隔离合同

入口在加载模型前执行以下断言：

1. 输入摘要、检测视图和 18 维旁路逐文件核对固定 SHA-256。
2. 检测视图必须精确包含 `2,560` 个唯一 `sample_id`，划分固定为训练 `2,048` 条、验证 `512` 条，且只含 TQH-C2 开发数据。
3. 基础文本只调用共享 B0 的 `render_input_text`，使用八个共同数值字段及其缺失掩码；标签、来源、划分、`profile`、传输族和协议置信度不得进入文本。
4. `split_id`、`binary_label`、`source_dataset` 和 `transport_family` 的唯一来源是检测视图。
5. 旁路原表中的 `split_id` 与 `transport_family` 只用于逐样本一致性断言；断言通过后严格投影为 `sample_id + 18` 维，再按检测视图顺序连接。
6. 旁路必须精确覆盖同一批样本，不能含重复、缺失或非有限数；五个不确定性不得为负，三个专家掩码必须为二值，协议置信度必须位于 `[0,1]`。
7. 四组输入装订后再次比较样本顺序、文本和标签摘要，任何组改变这些共同输入都会在模型加载前失败。
8. 输入绑定明确记录 `final_test_visible=false`，不接受最终测试或额外划分。

当前冻结输入摘要如下：

| 制品 | SHA-256 |
| --- | --- |
| `runs/r2-physics-sidecar-pilot/inputs/input-summary.json` | `028d18d41d5703b3792f6440948716edea43b6f45ddf1ebb427f816ebd829462` |
| `runs/r2-physics-sidecar-pilot/inputs/tqhc2/tqhc2-pilot-detection-view.parquet` | `6d8019dc15f2cd11abc2b4aa8a92ca81608b8000ef0c39eb83aae04607d9a126` |
| `runs/r2-physics-sidecar-pilot/inputs/tqhc2/tqhc2-pilot-sidecar.parquet` | `56658ea8886a57cdefe1dba2268e658f9072e24a94b93d5bf7a3711db9de2553` |

## 四组归因实现

四组都向同一个模型类传入 18 维旁路与一个非参数化旁路启用掩码：

| 组别 | 18 维输入 | 旁路启用掩码 | 生成规则 |
| --- | --- | ---: | --- |
| `T-A` | 全零 | `0` | 结构和参数保留，只关闭旁路贡献 |
| `T-P` | 真实旁路 | `1` | 保持样本级真实对应关系 |
| `T-S` | 置换旁路 | `1` | 在同来源、同传输族、同划分内置换完整 18 维向量，不读取标签 |
| `T-R` | 随机旁路 | `1` | 训练集逐维在同来源、同传输族训练池内置换；验证集逐维只从对应训练池抽样 |

`T-S` 和 `T-R` 直接复用现有 `r2_physics_sidecar_signal` 的置换与训练池随机合同，避免另写一套负对照语义。四组分别登记训练和验证旁路数组摘要及旁路启用掩码摘要。

## 模型融合

1. 基座固定为本地已有的 `distilbert/distilbert-base-multilingual-cased`，入口拒绝未核验或需要运行时下载的模型来源。
2. 文本分类表示沿用 DistilBERT 的首词元表示、`pre_classifier`、激活和分类头。
3. 新增唯一一个 `Linear(18, 768, bias=False)` 旁路投影，不新增注册表或工厂。
4. 不确定性门控固定为：

```text
gate = sidecar_mask * clamp(1 - mean(state_uncertainty_q0:q4), 0, 1)
fused = text_representation + gate * sidecar_projection(sidecar)
```

5. `T-A` 的投影层仍存在且参与相同参数计数，但因输入全零且掩码为零，对分类表示的旁路贡献严格为零。
6. 每组模型构造后登记总参数量、可训练参数量、逐参数形状摘要和投影参数量；共享结构合同要求四组逐项一致。
7. 每组都以相同种子重新初始化。首次新运行还比较 `pre_classifier`、分类头和旁路投影的初始化摘要，防止四组初始头部权重漂移。

## 训练、检查点与制品

三份配置只改变种子、种子输出目录、运行名称和种子标签。其余科学参数固定为已有 DistilBERT 基线预算：

- 每设备训练批量 `16`；
- 每设备验证批量 `64`；
- 梯度累积 `2`；
- 学习率 `2e-5`；
- 权重衰减 `0.01`；
- 训练 `3` 轮；
- 预热比例 `0.1`；
- 最大梯度范数 `1.0`；
- 每 `20` 个优化步保存检查点，运行中只保留最新 `1` 个；
- 每组固定 `192` 个优化步。

优化器运行时断言精确覆盖全部可训练参数且没有重复参数。每个检查点原子保存：

- DistilBERT 权重、配置和分词器；
- 18 维无偏置投影权重和融合配置；
- 优化器、调度器、混合精度缩放器；
- Python、NumPy、PyTorch 和 CUDA 随机状态；
- 当前步、下一轮和下一批位置；
- 当前最佳开发验证模型与完整制品哈希。

模型只在 `512` 条开发验证上按宏平均 F1 选模。最终仍只评价同一开发验证，输出预测、宏平均 F1、平衡准确率、良性误报率、Brier 分数、期望校准误差、吞吐和延迟。入口不读取任何外部或最终测试。

固定输出根为：

```text
runs/r2-transformer-sidecar-probe/distilbert-v0/
```

每个种子使用 `seed-42/43/44` 子目录，每组使用 `t-a/t-p/t-s/t-r` 子目录。单组运行中保留配置快照、输入绑定、模型绑定、运行绑定、原子状态、环境、控制台日志、在线跟踪原始日志、逐步指标、最新检查点、最佳选模模型、验证预测、指标和成本。单组成功后只在当前组目录内删除全部 `checkpoint-*`、其中的优化器状态及非最佳选模目录，再基于清理后的文件写最终制品清单。四组全部验收后才写种子汇总。

## 独立复审修复

1. `run_binding.json` 已升级为 `flow_probe_r2_distilbert_sidecar_run_binding_v2`，除主入口自身 SHA-256 外，还固定记录 `r2_physics_sidecar_signal.py`、`r2_protocol_contract.py`、`shared_b0_view.py`、`shared_b0_distilbert_baseline.py` 和 `tracking.py` 的 SHA-256。新运行与恢复运行都逐对象严格比较完整绑定，任一语义依赖变化都会拒绝复用旧目录。
2. `failed` 状态仅在 `resume_from_checkpoint=auto`、完整运行绑定一致且当前组目录内存在合法检查点时允许恢复。恢复继续使用原组目录并创建新的 SwanLab attempt；旧 attempt、旧失败原因、恢复来源检查点均保留在原子状态中。没有合法检查点的失败状态继续拒绝覆盖。
3. 每轮产生新最佳模型时立即删除本组旧选模模型；单组完成最终验证后删除本组全部训练检查点和 `training_state.pt`，把 `latest_checkpoint` 置空，仅保留最佳模型与最终评价必要制品。删除函数拒绝符号链接、组根目录及当前组目录之外的路径。
4. 三份配置升级为 `flow_probe_r2_distilbert_sidecar_probe_config_v2`，固定 `seed_execution=serial`、`save_total_limit=1`、`minimum_free_bytes=5 GiB` 和单次制品写入预留 `2 GiB`。三个种子共享非阻塞文件锁，并发启动会在加载模型前失败；入口在种子启动、每组启动、最佳模型保存和检查点保存前要求至少 `7 GiB` 可用空间，从而在单次受控写入后保留至少 `5 GiB` 安全余量。
5. 修复成功收尾的不可恢复窗口。训练与最终验证完成后先原子写入同绑定 `finalization_receipt.json`，其中固定运行标识、最佳模型相对路径、参数合同及完成所需制品哈希；状态随后进入 `finalizing`。入口再生成并校验 `best_model_receipt.json` 及排除瞬态目录的 `artifact_manifest.json`，确认两份收据和持久制品完整后，才删除当前组内的 `checkpoint-*`、受控 `.checkpoint-*.partial`、非最佳选模目录和受控 `.epoch-*.partial`，最后原子把状态置为 `finished` 并清空 `latest_checkpoint`。
6. `finalizing` 收尾可重入。若进程在最终清单生成、校验或清理阶段中断，即使训练检查点已经删除，下一次同绑定启动也会依据收尾收据恢复参数合同与最佳模型，重新生成和校验最终清单，幂等完成剩余清理，不会重新训练。收尾异常只记录失败原因并保持 `finalizing`；删除函数仍拒绝符号链接、组根目录和当前组之外的路径，部分目录名称还必须满足运行器生成的数字步数与 32 位十六进制标识合同。

## 验证记录

独立复审修复后按本轮约束只执行了一次 Python 编译命令：

```text
python3 -m py_compile src/flow_probe/r2_distilbert_sidecar_probe.py
退出码：1
```

失败发生在解释器进入源码编译前：系统 Python 尝试创建 `~/Library/Caches/com.apple.python/...` 缓存目录，被当前沙箱以 `PermissionError: [Errno 1] Operation not permitted` 拒绝；该结果不是源码语法错误证据。本实现代理没有重跑。主代理随后显式把字节码缓存改到可写目录并完成有效编译检查：

```text
PYTHONPYCACHEPREFIX=/tmp/codex-pycache python3 -m py_compile src/flow_probe/r2_distilbert_sidecar_probe.py
退出码：0
```

修复后语法门禁据此通过。另已通过只读定点回读核对新增常量、配置解析、完整运行绑定、失败恢复条件、SwanLab attempt 记录、组内安全删除、成功清理调用和串行入口的结构。

`finalizing` 可恢复收尾补丁落盘后只执行了一次指定缓存目录的编译检查：

```text
PYTHONPYCACHEPREFIX=/tmp/codex-pycache python3 -m py_compile src/flow_probe/r2_distilbert_sidecar_probe.py
退出码：0
```

本轮没有运行其他格式化、静态检查、测试、真实导入或 GPU 命令。

以下记录属于独立复审前的初版实现，不代表本轮修复后的编译结果。

只执行了一次不导入模型、不读取配置、不启动训练的 Python 编译检查：

```text
python3 -m py_compile thesis/experiments/llm_probe/src/flow_probe/r2_distilbert_sidecar_probe.py
退出码：0
```

只读输入核对确认：

- 检测视图与旁路实际 SHA-256 等于配置固定值；
- 检测视图实际为 `2,560` 行，旁路实际为 `2,560` 行；
- 检测视图划分为训练 `2,048`、验证 `512`；
- 旁路实际模式为元数据加固定 18 维；
- 当前五个不确定性存在大于 `1` 的合法先导值，因此门控在计算图中显式截断到 `[0,1]`，没有错误地把输入强制限定到 `[0,1]`。

源码只读自检曾发现一次补丁追加点落入跟踪上下文异常分支，根因是补丁锚点不唯一；已用精确块修复后再执行上述编译检查。

按任务约束未执行：

- Black、Ruff、Prettier 或其他格式化；
- Pyright 或其他静态类型检查；
- pytest、测试驱动开发或独立冒烟；
- 配置解析或输入绑定的独立运行；
- Git 差异命令；
- GPU、模型下载、正式训练或 SwanLab。

## 风险与启动边界

1. 入口尚未经过真实 PyTorch、Transformers、CUDA 和 SwanLab 运行，实际可执行性必须由独立代码复审和后续正式入口中的运行时断言共同确认。
2. 当前阶段只使用 TCP/UDP 主导的 TQH-C2 开发先导。QUIC 估计器仍未闭合，本实现不能解释为三协议正式 R2 已完成。
3. 这 12 组仅用于判断当前 18 维旁路能否在小型 Transformer 上形成稳定的开发集增量，不进入论文主表，也不替代正式三种子三源验证。
4. 实际 GPU 运行前必须单独告知用户：任务为三种子四组 DistilBERT 探针，预计峰值显存 `3—5 GB`，RTX 5090 总墙钟预计 `15—30` 分钟，并确认服务器已开机及费用性质。
5. 只有 `T-P` 在种子 42、43、44 上稳定优于 `T-A`、`T-S` 和 `T-R`，才能进入 Qwen；不得依据结果改种子、样本、旁路维度、学习率或验证划分。
