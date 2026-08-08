# 任务 02：普通 Qwen 构建路径行为等价提取报告

## 任务范围

- 需求来源：`task_plan.md` 的任务 02 与 `implementation-input.md` 第 4.1、7.2 节。
- 修改范围：`train_sft.py`、`test_train_sft.py` 和本报告。
- 未运行本机 `pytest`，未运行格式化，未提交，未推送。

## 编辑前差异审计

- 当前分支：`codex/ns3-pinn-m012-20260720`。
- 编辑前 `train_sft.py` 与 `test_train_sft.py` 均已有未提交改动。
- 既有改动新增 `attention_backend` 与 `group_by_length`，并已覆盖配置校验、训练绑定、运行跟踪、模型加载和测试。
- 上述改动与任务 02 不冲突。本任务保留其默认值、配置语义和绑定行为，并把两个字段纳入提取后的公共构建路径。
- 未覆盖、回滚或改写白名单外文件。

## 实现内容

### 普通 Qwen 公共构建路径

`src/flow_probe/train_sft.py` 新增或公开以下稳定构建层：

- `build_quantization_config_kwargs`：冻结 NF4、双重量化和 BF16 计算类型参数。
- `build_model_load_kwargs`：冻结量化模型加载参数，并保留 `attention_backend` 的 `auto`、`sdpa` 与 `flash_attention_2` 语义。
- `build_lora_config_kwargs` 与 `build_lora_config`：冻结普通 Qwen 的 LoRA 参数。
- `build_optimizer_scheduler_kwargs`：显式冻结 `paged_adamw_8bit`、线性调度、零预热和梯度裁剪默认值。
- `load_training_records`：按 JSONL 文件顺序加载完整记录，不丢弃 `sample_id`。
- `build_chat_training_record`、`build_chat_training_records` 与 `build_chat_dataset`：复用原聊天模板和补全末尾 EOS 逻辑；`sample_id` 仅保留为数据集元数据。
- `build_qwen_model_and_tokenizer`：复用原分词器、填充令牌、量化和模型加载顺序。
- `build_sft_trainer`：继续通过 `SFTTrainer(peft_config=...)` 挂载 LoRA，复用原训练参数、随机种子和回调。

普通 `_train_impl` 已改为调用上述构建函数。原命令行、配置读取、输出目录、训练绑定、检查点发现、自动恢复、运行状态和制品写入路径未变。

公共文件没有导入物理旁路、状态头或 PINN 损失模块。

### 行为等价与隔离测试

`tests/test_train_sft.py` 新增三组回归测试：

1. 核对量化、模型加载、LoRA、优化器、调度器、梯度裁剪、最大长度和长度分组参数。
2. 核对 JSONL 加载与聊天样本均保留 `sample_id`，同时确认该标识不进入提示词或补全文本。
3. 对固定样本比较重构前后的聊天文本、令牌、标签掩码和截断结果。

既有生成加速测试与断点恢复测试均保留。

## 静态验证

以下验证均设置 `PYTHONDONTWRITEBYTECODE=1` 并使用 `python3 -B`，不写入字节码缓存。

| 验证 | 结果 |
| --- | --- |
| 对 `train_sft.py` 与 `test_train_sft.py` 执行 AST 解析 | 通过，`AST_OK 2` |
| 使用系统 Python 直接导入 `flow_probe.train_sft` | 未完成，本机缺少既有依赖 `PyYAML`，停止于 `ModuleNotFoundError: yaml` |
| 仅在进程内提供 `yaml` 模块替身后导入公共 API | 通过，11 个公共构建/加载函数均可调用 |
| 量化、模型加载、优化器/调度器与 `sample_id` 隔离纯函数核验 | 通过，`BEHAVIOR_OK` |
| 固定样本聊天文本、令牌、标签掩码与截断等价核验 | 通过，截断长度 35，受监督补全令牌 5 个 |
| AST 检查公共文件无物理模块导入，且 `_train_impl` 调用公共构建路径 | 通过 |
| `git diff --check` | 通过 |

未执行：

- 本机 `pytest`：项目规则明确禁止。
- Black 或其他格式化：任务计划与分派明确禁止。
- 真实 `transformers`、`peft`、`datasets`、`trl` 对象构造：本机依赖环境不完整。

## 风险与后续门禁

- 服务器必须运行 `uv run --no-sync pytest -q tests/test_train_sft.py`，才能确认真实 TRL 数据预处理、LoRA 挂载及全部既有恢复测试。
- `sample_id` 作为额外数据集列由 TRL 的正常未使用列处理路径移除；真实版本兼容性由上述服务器目标测试确认。
- 线性调度、零预热和 `max_grad_norm=1.0` 是原 `SFTConfig` 的解析后默认值，本次将其显式冻结；服务器等价测试应复核解析后的训练参数不变。
- 本报告不宣称服务器测试通过，也不放行正式训练。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/train_sft.py`
- `thesis/experiments/llm_probe/tests/test_train_sft.py`
- `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/report-task-02-sft-parity.md`

## 修复轮次 1

### 审查发现处理

1. 删除逐字节 `_ParityTokenizer` 与手写标签快照自证，改用服务器本地 Qwen3-1.7B 快速分词器、TRL 0.29.1 的 `SFTTrainer._prepare_dataset` 和 `DataCollatorForLanguageModeling`。旧路径参考实现独立保留原格式化逻辑，不调用待测聊天构建函数。测试覆盖一条未截断样本和一条截断后仍保留 4 个补全监督令牌的样本，逐项比较 `input_ids`、`completion_mask`、最终 `labels` 和长度。
2. 新增严格构造器接线测试，记录 `AutoTokenizer`、`BitsAndBytesConfig`、`AutoModelForCausalLM`、`LoraConfig`、`SFTConfig` 与 `SFTTrainer` 的实际参数，覆盖无填充令牌与已有填充令牌两种分支。测试同时证明 `sample_id` 在 `Dataset` 和 TRL 预处理数据集中按顺序保留，但不会进入整理后的模型批次；另以严格替身证明 `_train_impl` 必须调用公共模型、记录加载、聊天数据集和训练器构建路径。

### 本轮文件变化

- `train_sft.py`：本轮未修改，保留已审查的公共构建实现和既有加速字段。
- `test_train_sft.py`：替换两项不足的手写测试，新增真实 TRL/Qwen 行为测试和严格构造器接线测试。
- 本报告：追加修复轮次记录。

### 本轮验证边界

- 已执行无缓存 AST 与静态结构核验，结果见最终任务回报。
- 未在本机运行 `pytest` 或格式化，未提交或推送。
- 真实 Qwen 分词器、TRL 预处理、整理批次和完整测试必须在服务器锁定环境执行；本报告不提前宣称其通过。
