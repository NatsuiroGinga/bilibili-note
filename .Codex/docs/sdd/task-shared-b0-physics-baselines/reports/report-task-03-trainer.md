# 任务 03：共同状态头、物理调度与可恢复训练器实施报告

## 当前结论

- 状态：`formal_interface_revised`、`server_revalidation_pending`、`review_pending`。
- 配置、训练器和 23 项专项测试已经实现；本报告已补齐。
- 正式训练接口修复后的唯一一次精确范围 `Pyright` 已通过，结果为 `0 errors, 0 warnings, 0 informations`。
- 本机项目环境缺少 `torch`；服务器锁定的 `uv` 环境已完成真实模块导入、精确失败节点和完整专项测试。
- 上一轮服务器 `28 passed` 只证明修复前版本；本轮修改生产训练入口后必须由主代理重新运行服务器目标测试，不能沿用旧结果宣称当前版本通过。
- 按当前门禁，行为测试、数据与绑定哈希、必要冒烟和运行目录隔离通过后即可启动实验并保留 `review_pending`，不等待独立复审；若后续复审发现严重或重要问题，必须停止并作废对应结果。

## 任务范围

本任务只新增以下四个白名单文件：

- `thesis/experiments/llm_probe/configs/shared_b0_physics_baselines_seed42_200_v1.yaml`
- `thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_train.py`
- `thesis/experiments/llm_probe/tests/test_shared_b0_physics_train.py`
- `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/report-task-03-trainer.md`

未修改任务 01、任务 02、冻结分类数据、物理旁路制品、历史运行目录或公共物理公式文件。未提交，未推送，未启动 GPU 训练。

## 冻结配置

新配置固定以下合同：

- 模型：服务器本地 `Qwen3-1.7B`，共同字段视图 `shared_b0_common_v1`。
- 随机种子：`42`。
- 优化步数：`200`；保存间隔：`20`；梯度裁剪：`1.0`。
- 主生成批量：微批 `2`、梯度累积 `2`；硬件回退：微批 `1`、梯度累积 `4`；有效批量均为 `4`。
- 生成位置：`800`；物理记录：`2421`；物理微步：`400`。
- 状态锚点：`5`；每条有效监督锚点：`2`；模式：`anchor0_plus_one`。
- `lambda_state=1.0`；状态监督分支 `lambda_physics=0.0`；标准 PINN 分支 `lambda_physics=0.01`。
- 分类输入只绑定冻结 `qwen_train.jsonl`，物理旁路只绑定独立 `ns3_physics_train.jsonl`，普通 Qwen 可见字段严格为八个已发布共同字段。
- 两条基线使用不同且固定的输出目录，配置状态为 `review_pending`。

## 训练器实现

### 公共 Qwen 路径

训练器直接复用任务 02 的以下公共接口：

- `build_qwen_model_and_tokenizer`
- `build_chat_dataset`
- `build_chat_training_records`
- `build_sft_trainer`
- `build_training_settings`
- `build_optimizer_scheduler_kwargs`
- `build_training_binding`

模型加载、NF4 量化、LoRA 挂载、聊天模板、补全标签、优化器、线性调度器和梯度裁剪沿用普通 Qwen 路径。状态头在公共训练器创建后、优化器创建前挂载，并检查全部状态头参数确实进入同一个优化器。

### 状态头与损失

- 直接复用 `ContinuousQueueStateHead`、`masked_state_target_loss`、`select_last_token_hidden` 和 `queue_balance_residual`，没有复制状态损失或队列平衡公式。
- 状态头只读取普通 Qwen 提示词前向的最后有效令牌隐藏状态，输出五锚点连续队列状态。
- 状态损失按有效掩码逐元素归约。
- 状态监督分支只构造状态目标和状态掩码，不读取容量、接收、出队、丢弃或归一化尺度。
- 标准 PINN 分支才把累计物理量恢复为四窗口系数，并增加 `0.01 * queue_balance_residual.square().mean()`。
- 物理微批均值乘以 `actual_batch_size / (2421 / 400)`，保证六样本批和七样本批按记录等权。
- 损失或梯度出现非有限数时立即失败；裁剪前记录联合梯度二范数。

### 签名状态掩码裁决

原计划文字要求重新调用 `build_state_supervision_masks`，但任务 01 已发布并验签的 `state_mask_inputs` 使用 `sample_id` 确定；现有辅助函数按 `group_id` 构造。重新计算会使训练消费的掩码与任务 01 的签名旁路不一致。

经主代理裁决，本任务执行以下更严格的数据合同：

- 实际损失直接消费旁路中已验签的 `state_mask_inputs`。
- 每条掩码必须恰为五个布尔值。
- `anchor0` 必须为真。
- 每条必须恰有两个真值。
- 对完整掩码序列计算并绑定 `state_mask_sha256`。
- 改变 `group_id` 不得改变训练消费的掩码。

这是一项经裁决的计划修正，不是静默偏离。专项测试覆盖签名掩码消费、非法长度、非法类型、`anchor0` 缺失、真值数量错误和物理字段访问隔离。

### 冻结调度与绑定

- 生成调度在两种批量档位下共享同一条 800 个 `sample_id` 的扁平顺序；主档形成 400 个二样本微批，回退档形成 800 个单样本微批。
- 物理调度固定为 21 个七样本批和 379 个六样本批，共 400 个微步；2421 条记录各出现一次。
- 生成与物理调度分别保存完整顺序、批边界、顺序哈希、批边界哈希和综合调度哈希。
- 运行绑定扩展任务 02 的普通训练绑定，并加入配置、分类训练、分类验证、旁路、旁路清单、双调度、状态掩码、状态头初始化、LoRA 初始化、训练器代码、基线身份和损失权重哈希。
- 两条基线除 `baseline`、`lambda_physics` 和最终绑定哈希外，共享全部公共数据、顺序、初始化与训练参数。

### 检查点与运行目录

- 每 20 步以及受控短运行终点保存六位零填充检查点。
- 检查点包含 LoRA 适配器、LoRA 可训练参数、状态头、优化器、调度器、梯度缩放器、Python/NumPy/PyTorch/CUDA 随机状态、全部指标、双游标、绑定和进度。
- 恢复前先比较完整绑定，基线、权重、配置、数据、调度、初始化或代码任一变化均拒绝恢复。
- 新运行拒绝非空未知目录；显式检查点必须位于当前运行的 `checkpoints/`；已完成运行拒绝覆盖。
- 运行制品包含解析配置、环境、设备能力、训练绑定、生成顺序、物理调度、掩码审计、逐步指标、运行状态、最终适配器、最终状态头、训练摘要和制品清单。

## 专项测试覆盖

`tests/test_shared_b0_physics_train.py` 当前包含 23 个测试函数，并通过参数化覆盖更多输入组合，主要检查：

1. 真实配置与两条语义基线合同。
2. 仅允许 `2x2` 与 `1x4` 两种有效批量档位。
3. 两档生成调度共享 800 个位置及顺序。
4. 物理调度的 `21x7 + 379x6` 批边界和单次完整覆盖。
5. 生成与物理双游标。
6. 签名掩码直接消费和状态分支物理字段隔离。
7. 掩码状态损失与手算结果一致。
8. 标准 PINN 只增加既有残差的 `0.01` 倍。
9. 物理残差梯度到达共享 LoRA 参数与状态头。
10. 六样本批和七样本批的逐记录等权。
11. 非有限损失与梯度立即失败。
12. 两条基线状态头初始化哈希相同。
13. 物理字段不进入普通 Qwen 提示词。
14. 两条绑定仅切换基线身份与物理损失权重。
15. 真实训练运行时严格接线到任务 02 公共构建接口。
16. 四步连续运行与两步保存、恢复到四步等价。
17. 基线或配置绑定错配在恢复参数前被拒绝。
18. 最终绑定包含普通 Qwen 绑定和全部调度哈希。
19. 正式命令必须显式提供唯一 `--output-dir`，预检模式可以不提供。
20. 绝对输出路径进入训练绑定，恢复时不能切换到其他目录。
21. SwanLab 固定使用 `mortiswang/malicious-traffic-llm` 在线项目并逐步记录全部必要标量。
22. 正常运行和失败运行分别调用对应结束接口，并在本地保留运行记录和日志目录。

## 本地验证

### 已通过

| 验证                                               | 结果                                                             |
| -------------------------------------------------- | ---------------------------------------------------------------- |
| 使用仓库外精确配置对训练器和专项测试运行 `Pyright` | `0 errors, 0 warnings, 0 informations`                           |
| 使用仓库外最小配置运行 `Black`                     | 训练器与测试均格式化完成；最终复核训练器 `1 file left unchanged` |
| 统计专项测试函数                                   | `20` 个                                                          |

最终 `Pyright` 命令：

```bash
.venv/bin/pyright --project /private/tmp/shared-b0-pyright.json
```

当前工作区的 `pyproject.toml` 存在重复 `[tool.pyright]` 段，直接运行 `Pyright` 和 `Black` 会在读取配置时失败。该文件不在任务白名单内，本任务没有修改；最终检查使用 `/private/tmp` 下的精确临时配置，且只包含本任务训练器与测试文件。

### 环境性阻塞

真实导入命令：

```bash
PYTHONPATH=src .venv/bin/python -B -c \
  'import flow_probe.shared_b0_physics_train as module; print(module.CONFIG_SCHEMA_VERSION)'
```

结果停在 `import torch`，错误为 `ModuleNotFoundError: No module named 'torch'`。本机项目 `.venv` 没有安装 `torch`，因此该结果不能判断服务器真实导入或运行行为。

按照更新后的规则，未把 AST 解析作为交付门禁，也未在规则更新后继续执行 AST 检查。规则明确前的历史解析结果不计入本报告的通过项。

### 未执行

- 本机 `pytest`：计划要求 Python 测试只在服务器项目 `uv` 环境运行，本机同时缺少 `torch`。
- 真实 Qwen、TRL、PEFT、bitsandbytes 和 CUDA 构造。
- 两条两步 GPU 冒烟。
- 四步连续与两步恢复的真实 GPU 等价检查。
- 200 步正式训练、公开检测评估和训练拟合物理诊断。

## 服务器验收与启动门禁

同步后至少执行：

```bash
uv run --no-sync python -B -c \
  'import flow_probe.shared_b0_physics_train as module; print(module.CONFIG_SCHEMA_VERSION)'
uv run --no-sync pytest -q tests/test_shared_b0_physics_train.py
```

随后执行：

1. 验证旁路文件、旁路清单、冻结分类文件和运行绑定哈希。
2. 确认两条输出目录相互隔离且均为空，不覆盖历史运行。
3. 分别运行两条两步冒烟，核对状态监督分支不访问物理系数，标准 PINN 分支确实访问并记录物理残差。
4. 核对两步检查点包含完整文件集合，恢复绑定一致。
5. 运行四步连续与两步保存、恢复到四步的等价检查。

上述行为测试、数据与绑定哈希、必要冒烟和目录隔离通过后，可将正式实验保持为 `review_pending` 并立即启动，不等待独立复审。服务器任一门禁失败时不得启动；后续复审发现严重或重要问题时，必须停止并作废受影响运行。

## 遗留风险

- 本机缺少真实深度学习依赖；服务器已提供真实导入与完整专项测试证据。
- TRL 预处理后的 `sample_id` 保留、状态头进入 paged AdamW、PEFT 适配器保存以及 BF16 前向需要由服务器专项测试和两步冒烟确认。
- 签名掩码裁决与原计划中“重新调用 `build_state_supervision_masks`”的字面要求不同，独立复审必须确认主代理裁决已被正确记录和贯彻。
- 任务 03 的真实导入与专项测试已通过；正式训练仍需通过数据与绑定哈希、两条两步冒烟、真实恢复等价和输出目录隔离门禁。

## 正式训练接口修复

上一轮实现虽然支持程序化注入 `MetricLogger`，但命令入口没有创建 SwanLab 在线运行；同时正式命令只能读取配置中的固定输出目录，不能把本次唯一运行目录显式绑定到训练、恢复和制品。这会导致正式运行没有云端逐步图表，也无法由启动方可靠地区分不同尝试。

本轮只修改训练器、专项测试和本报告，完成以下修复：

- 正式 CLI 新增并强制要求 `--output-dir`；`--preflight-only` 仍可省略该参数。
- 显式目录贯穿公共 `TrainingSettings`、真实训练器、运行布局、恢复目录和解析配置，并以绝对路径进入运行绑定哈希。
- 目录仍执行原有非空未知目录拒绝、完成运行拒绝覆盖和检查点只能位于当前运行目录的门禁。
- SwanLab 工作区固定为 `mortiswang`，项目固定为 `malicious-traffic-llm`，模式固定为 `online`。
- 每个优化步在线记录优化步、生成损失、状态损失、物理损失、总损失、梯度范数、非有限数及已有的学习率和双游标等标量。
- 正常结束调用 `finish()`；训练异常调用 `finish(state="crashed", error=...)`，并额外记录最后完成步和异常是否属于非有限数。
- 本地保存 `console.log`、`swanlog/train/`、`swanlab_run.json` 和逐步 `step_metrics.jsonl`；制品清单延后到控制台与 SwanLab 日志关闭后再计算哈希。失败运行也生成状态为 `failed` 的制品清单。

本轮新增三个测试函数，覆盖正式 CLI 目录要求、在线逐步指标与正常结束、异常结束与本地记录。按规则未在本机运行 `pytest`，服务器测试由主代理执行。

本轮唯一一次静态检查命令：

```text
.venv/bin/pyright --project /private/tmp/shared-b0-pyright.json
0 errors, 0 warnings, 0 informations
```

根据最新任务规则，本轮取消真实导入检查；未运行 AST、Prettier、Black、Ruff、其他格式化、本机 `pytest`、GPU 冒烟、恢复短跑或正式训练。

## 服务器修复轮次 1

服务器首次真实导入通过；专项测试得到 `27 passed, 1 failed`。唯一失败发生在标准 PINN 数值测试：测试把 `requires_grad=True` 的张量直接传给 `pytest.approx`，后者尝试转换为 NumPy 数组并触发 `RuntimeError`。生产损失和物理公式没有失败。

本轮只修改专项测试的比较方式：

- 数值等价比较统一使用 `tensor.detach().item()` 后的标量。
- 单独断言 `result.physics.requires_grad`，避免脱离计算图后的数值比较掩盖可求导性。
- 对 `result.total` 执行反向传播，并确认预测张量获得有限且非零梯度，保留总损失梯度通路门禁。
- 未修改生产训练器或物理公式。

可复用故障规则：**不得把需要梯度的 PyTorch 张量直接交给 `pytest.approx` 或其他可能隐式调用 NumPy 的比较器。数值比较应先 `detach()` 并转换为标量；可求导性和梯度通路必须用独立断言验证。**

本轮按分派要求未运行 AST、格式化或本机 `pytest`。服务器应先重跑精确失败节点，再重跑完整专项文件。

## 服务器专项验收

修复同步后，服务器锁定环境得到以下最终结果：

- 真实导入：通过。
- 精确节点 `test_standard_pinn_only_adds_point_zero_one_times_existing_residual_loss`：`1 passed`。
- 完整 `tests/test_shared_b0_physics_train.py`：`28 passed`。
- 生产训练器和物理公式在修复轮次中未修改。

因此，任务 03 不再存在导入或专项单元测试阻塞。尚未完成的行为门禁是：

1. 对正式旁路、分类文件、清单和运行绑定执行哈希预检。
2. 确认状态监督与标准 PINN 输出目录相互隔离、为空且不覆盖历史运行。
3. 两条基线分别完成两步真实 GPU 冒烟，并核对字段访问、损失分支、检查点和日志。
4. 完成四步连续运行与两步保存、恢复到四步的真实等价检查。

以上门禁通过后即可保持 `review_pending` 启动实验，不等待独立复审；后续若复审发现严重或重要问题，再停止并作废受影响结果。
