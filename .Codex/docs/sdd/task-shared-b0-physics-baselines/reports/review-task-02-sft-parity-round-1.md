# 任务 02 修复轮次 1 定向复审

## 结论

**通过定向复审。原两项重要发现均为 `ADDRESSED`。**

- 严重问题：0 项。
- 重要问题：0 项。
- 建议问题：0 项。
- 修复轮次仅修改 `tests/test_train_sft.py`；`src/flow_probe/train_sft.py` 的 SHA-256 仍为首轮审查登记的 `2c432c26c0d21a3428f26a28b51b87ea9216f206a733d4dcc2b5baa3bddc0745`。
- 当前 `tests/test_train_sft.py` 的 SHA-256 为 `85a028b535b2b904f0d1840a9295fc92fd07fd89e3ddb60a3c4a68d926b029ef`。
- 在本轮指定范围内，任务 02 已具备解除原两项审查阻塞的证据。

## 复审范围与证据

- 合同依据：`task_plan.md` 任务 02、`implementation-input.md` 第 4.1 节和第 7.2 节。
- 历史依据：`report-task-02-sft-parity.md`、其中“修复轮次 1”追加记录，以及 `review-task-02-sft-parity.md` 的两项重要发现。
- 代码范围：`src/flow_probe/train_sft.py`、`tests/test_train_sft.py`。
- 锁定依赖：`uv.lock` 将 `trl` 固定为 `0.29.1`。
- 服务器完整目标测试：`uv run --no-sync pytest -q tests/test_train_sft.py`，结果为 `37 passed in 5.53s`，退出码为 `0`。
- 服务器新增精确节点：两项新增测试合计 `2 passed in 4.94s`，退出码为 `0`。
- 服务器日志根：`runs/validation/shared-b0-task02-sft-parity-fix1-20260731T082016Z/`。
- 本轮按分派要求没有运行本机 `pytest` 或格式化。
- 只读抽象语法树检查通过：旧参考函数不调用任何待测聊天构建函数；真实等价测试包含本地分词器、真实 TRL 预处理和整理器路径；严格接线测试调用 `_train_impl`；生产 `_train_impl` 调用四个公共构建边界。

## 原发现裁决

### 1. 真实 Qwen、TRL 预处理与独立旧参考等价证明

**裁决：`ADDRESSED`。**

证据如下：

- `tests/test_train_sft.py:35` 固定服务器本地 Qwen3-1.7B 分词器目录；第 479 至 484 行要求目录存在，并以 `use_fast=True`、`local_files_only=True` 加载，未回退到逐字节替身或联网模型。
- `_legacy_chat_training_record` 在第 98 至 111 行独立保留重构前的聊天模板与补全末尾 EOS 逻辑；`_legacy_chat_dataset` 在第 114 至 119 行独立构造 `Dataset`。两者均不调用 `build_chat_training_record`、`build_chat_training_records` 或 `build_chat_dataset`，不构成同源自证。
- `_prepare_with_real_trl` 在第 122 至 149 行直接调用锁定版本 `SFTTrainer._prepare_dataset`；测试在第 477 行导入并在第 536 至 543 行实际调用 `DataCollatorForLanguageModeling`。
- 夹具同时覆盖未截断样本和截断样本。测试先证明短样本未达到上限、长样本超过上限，再将长样本截断到提示词令牌长度加 4，并断言截断后仍有 4 个补全监督令牌。
- 两条独立路径逐条比较 `input_ids` 与 `completion_mask`；整理后比较 `input_ids` 与最终 `labels`；同时核对未截断长度、截断后最终长度和补全监督令牌数。
- 对应新增精确节点已在服务器真实依赖环境通过，不再只是静态存在的未执行测试。

### 2. `sample_id` 批次隔离与 `_train_impl` 公共路径不可绕过证明

**裁决：`ADDRESSED`。**

证据如下：

- 真实等价测试直接调用 `build_chat_dataset`，第 525 行按输入顺序断言原始 `Dataset` 保留全部 `sample_id`，第 526 行断言真实 TRL 预处理后的数据集仍保留同一顺序。
- 同一测试把真实预处理记录交给 TRL 整理器，第 544 至 546 行证明整理后的模型批次与旧路径令牌、标签一致且不含 `sample_id`；第 547 至 553 行进一步断言传入模型的键严格为 `attention_mask`、`input_ids` 和 `labels`。
- 严格构造器测试在第 294 至 407 行记录并核对 `AutoTokenizer`、`BitsAndBytesConfig`、`AutoModelForCausalLM`、`LoraConfig`、`SFTConfig` 和 `SFTTrainer` 的实际参数，覆盖分词器无填充令牌和已有填充令牌两条分支，并核对量化、模型加载、LoRA、随机种子、优化器、调度器、梯度裁剪、注意力后端、长度分组、数据集和回调接线。
- 该测试在第 409 至 470 行替换模块级公共构建函数后实际调用 `_train_impl`，严格断言模型构建、两次记录加载、两次聊天数据集构建和训练器构建的调用顺序及数据传递。若入口内联或绕开任一公共边界，预期调用序列或哨兵对象将不成立，测试会失败。
- 生产 `_train_impl` 的只读抽象语法树和源码均确认调用 `build_qwen_model_and_tokenizer`、`load_training_records`、`build_chat_dataset` 和 `build_sft_trainer`；服务器新增精确节点已通过。

## 新增问题检查

修复差异没有改动生产代码，只以真实依赖测试替换原手写自证，并增加严格构造器与入口接线测试。未发现新增的正确性、数据泄漏、凭据、性能或可维护性严重/重要问题。

## 未修改与验证边界

- 本轮复审未修改生产代码、测试、配置、运行制品或原实现报告。
- 本轮仅新增本复审报告。
- 未运行本机 `pytest`、格式化或服务器命令；服务器结果由主代理补充，并已记录对应命令、退出码和唯一日志根。
