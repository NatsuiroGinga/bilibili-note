# 任务 02 独立审查：普通 Qwen 构建路径行为等价提取

## 结论

**请求修改，暂不放行任务 03。**

- 严重问题：0 项。
- 重要问题：2 项。
- 建议问题：0 项。
- **服务器目标测试允许执行，且已执行通过；但现有测试集合不足以完成任务 02 的行为等价验收。**
- 当前静态差异中未发现已确认的普通 Qwen 运行行为漂移；两项重要问题均属于关键行为没有被可证伪测试覆盖。若据此直接进入物理训练器集成，普通基线的令牌、标签或旁路隔离一旦发生无声变化，后续实验结果将缺少有效性依据。

## 审查范围与证据

- 审查文件：`src/flow_probe/train_sft.py`、`tests/test_train_sft.py`。
- 合同依据：`task_plan.md` 任务 02、`implementation-input.md` 第 4.1、7.2 节及实现报告。
- 当前文件 SHA-256：
  - `train_sft.py`：`2c432c26c0d21a3428f26a28b51b87ea9216f206a733d4dcc2b5baa3bddc0745`
  - `test_train_sft.py`：`4de338398da65057a8765a40c8d2f18eb38523344064cc085c5863b8a4842978`
- 上述哈希与服务器同步后文件一致。
- 服务器证据：`uv run --no-sync pytest -q tests/test_train_sft.py` 得到 `37 passed in 0.14s`，退出码为 `0`；日志根为 `runs/validation/shared-b0-task02-sft-parity-20260731T075756Z/`。
- 本次独立审查没有运行本机 `pytest` 或格式化。
- 只读 AST 检查通过：`_parse_args` 与 `main` 相对 `HEAD` 的抽象语法树不变；`_train_impl` 调用提取后的模型、数据集和训练器构建函数；公共文件没有物理旁路、状态头或 PINN 模块导入。
- `git diff --check` 对两个审查文件无输出。

## 已确认符合合同的部分

- 原命令行仍只接受 `--config` 与可选 `--model-path`，配置读取、普通训练输出目录和入口调用顺序未变。
- `attention_backend` 仍默认 `auto`，只在非 `auto` 时传入 `attn_implementation`；`group_by_length` 仍默认 `False` 并传入 `SFTConfig`。两项既有加速改动继续进入配置校验、训练跟踪和训练绑定。
- NF4、双重量化、BF16、`device_map=auto`、LoRA 秩/缩放/丢弃、`all-linear`、`paged_adamw_8bit`、线性调度、零预热、梯度裁剪、随机种子和数据随机种子均已进入提取后的构建路径。
- `load_training_records` 按 JSONL 原顺序保留完整记录；`build_chat_training_record` 只用原有 `prompt` 和 `completion` 构造可见文本，`sample_id` 仅作为单独元数据列保留。
- 当前代码没有把 `sample_id` 拼接进提示词或补全文本，也没有引用任何物理模块。

## 重要问题

### 1. 手写快照没有经过真实 TRL 预处理，无法证明令牌、标签掩码和截断等价

**位置：** `tests/test_train_sft.py:90`、`tests/test_train_sft.py:117`、`tests/test_train_sft.py:310`；对应生产路径为 `src/flow_probe/train_sft.py:732`、`src/flow_probe/train_sft.py:774`。

`_ParityTokenizer.encode` 只是把 UTF-8 字节转成整数；`_token_label_snapshot` 又在测试内部自行拼接字符串、切片并生成 `-100` 标签。生产路径没有调用这两个函数，而是把 `Dataset` 交给锁定版本的 TRL `SFTTrainer`，由其执行真实分词、补全掩码、截断和数据整理。

因此，当前测试实际证明的是“新旧字符串经过同一个测试辅助算法得到相同结果”，不能发现以下退化：

- 真实子词分词器在提示词与补全边界处产生不同令牌；
- TRL 的 `completion_mask` 或整理后的 `labels` 改变；
- `max_length` 没有传入实际训练器，或截断位置改变；
- 新公共构建函数保留不变，但 `_train_impl` 或 `SFTTrainer` 接线绕开它。

这不满足实施合同中“固定小样本的聊天文本、令牌、标签掩码和截断逐项相等”以及“测试能够证伪退化”的要求。

**最小可验收修复条件：**

1. 在服务器锁定依赖环境中新增一个纯 CPU 精确测试，分别用独立保存的旧格式化参考实现和当前提取路径构造同一批样本；参考实现不得调用待测的新聊天构建函数。
2. 两条路径都必须进入生产使用的 `datasets.Dataset`、TRL 预处理与数据整理路径，比较真实的 `input_ids`、`completion_mask`、整理后 `labels` 和最终长度，不能再用测试内手写标签算法替代。
3. 分词器使用服务器本地 Qwen 分词器，或使用带固定聊天模板且能体现子词边界效应的确定性快速分词器；不得继续使用逐字节编码替身。
4. 夹具至少覆盖一条未截断样本和一条在提示词/补全边界附近发生截断的样本，并确认截断后仍存在受监督补全令牌。
5. 精确测试和完整 `tests/test_train_sft.py` 均须在服务器通过。

### 2. 构建器接线与 `sample_id` 的数据集/批次隔离没有行为测试

**位置：** `tests/test_train_sft.py:240`、`tests/test_train_sft.py:287`；对应生产路径为 `src/flow_probe/train_sft.py:704`、`src/flow_probe/train_sft.py:732`、`src/flow_probe/train_sft.py:746`、`src/flow_probe/train_sft.py:767`、`src/flow_probe/train_sft.py:774`、`src/flow_probe/train_sft.py:827`。

当前测试只比较量化、模型加载、LoRA、优化器和调度器的字典，并只在 `build_chat_training_records` 返回的 Python 字典中检查 `sample_id`。它没有调用或严格替身化以下生产边界：

- `build_chat_dataset`；
- `build_qwen_model_and_tokenizer`；
- `build_lora_config`；
- `build_sft_trainer`；
- 真实 TRL 预处理后的数据集和一个实际整理批次。

因此，即使构造器参数没有真正传给模型或训练器、LoRA 没有挂载、`sample_id` 在预处理时丢失，或 `sample_id` 被传给模型可见批次，现有 37 项测试仍可能全部通过。只读 AST 可以确认当前 `_train_impl` 的调用关系，但 AST 断言不能替代可长期防退化的行为测试。

**最小可验收修复条件：**

1. 使用严格替身记录 `AutoTokenizer`、`BitsAndBytesConfig`、`AutoModelForCausalLM`、`LoraConfig`、`SFTConfig` 和 `SFTTrainer` 的实际调用，逐项断言模型、量化、LoRA、随机种子、优化器、调度器、梯度裁剪、`attention_backend`、`group_by_length`、训练/验证数据集和回调均由提取后的公共构建路径传入。
2. 覆盖“分词器没有填充令牌”和“已有填充令牌”两种情况，证明只在前者回退到 EOS，保持原路径行为。
3. 直接调用 `build_chat_dataset`，断言记录顺序不变且 `sample_id` 列仍存在，供物理旁路按标识连接。
4. 对除 `sample_id` 外完全相同的两条记录走真实 TRL 预处理和一个整理批次，断言两者的 `input_ids`、`completion_mask` 和 `labels` 逐项相等；同时断言传给模型的批次键不包含 `sample_id`。
5. 增加 `_train_impl` 的严格接线测试，或以等价的可执行构造测试证明生产入口确实使用这些构建器；仅检查纯参数字典或 AST 不足以验收。
6. 上述精确测试和完整 `tests/test_train_sft.py` 均须在服务器通过。

## 实验有效性与放行判定

- **服务器目标测试：允许，且当前哈希对应的 37 项测试已通过。** 该结果证明现有断言没有失败，不证明任务 02 的完整合同已经满足。
- **任务 02：不通过独立审查。**
- **任务 03：暂不放行。** 两项重要问题完成最小补测、服务器精确测试与完整目标测试通过，并由复审确认后方可集成。
- **实验有效性：存在未排除的重要风险。** 当前没有静态证据证明普通 Qwen 已经发生行为漂移；但真实令牌/标签/截断等价和 `sample_id` 批次隔离尚无可证伪证据，因此不得用当前状态启动或解释正式物理基线实验。

## 未修改内容

- 未修改 `train_sft.py`、`test_train_sft.py` 或其他生产代码、测试、配置与运行制品。
- 本次只新增本审查报告。
