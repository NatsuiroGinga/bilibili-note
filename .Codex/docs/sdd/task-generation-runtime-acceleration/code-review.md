# 生成式运行时加速代码审查

**日期：** 2026-07-30  
**结论：** 请求修改。未发现严重问题，发现 3 个重要问题。前两项阻塞依赖可靠断点续评的正式评测；第三项阻塞使用逐批显存指标选择候选批量。

## 重要问题

### 1. 部分预测日志不是批次级原子提交，断电后可能无法恢复或接受半批次

- 位置：`thesis/experiments/llm_probe/src/flow_probe/evaluate_model.py:447`、`thesis/experiments/llm_probe/src/flow_probe/evaluate_model.py:567`
- `append_batch()` 直接以追加模式写入整批 JSONL，再执行 `flush()` 和 `fsync()`。进程终止或主机断电仍可能发生在写入中间，留下若干完整行加一个截断尾行，或者只留下该批次的一部分完整行。
- 截断尾行会被 `_restore()` 当作损坏行直接拒绝，导致本应可恢复的运行永久无法续评；只有部分完整行落盘时，恢复逻辑又会把它们登记为已完成批次，随后以新批次补算剩余样本，使 `completed_batches` 可能超过 `total_batches`，并破坏批次耗时口径。
- 现有测试只模拟完整批次落盘后的恢复，没有覆盖写入中断窗口。部分日志需要采用临时文件加原子替换，或采用带批次提交标记且能安全丢弃未提交尾批次的日志协议。

### 2. 恢复时未校验完整预测行，合法 JSON 损坏可在发布后才失败

- 位置：`thesis/experiments/llm_probe/src/flow_probe/evaluate_model.py:458`、`thesis/experiments/llm_probe/src/flow_probe/evaluate_model.py:584`、`thesis/experiments/llm_probe/src/flow_probe/evaluate_model.py:751`
- `_register_restored_row()` 只校验 `record_index`、`sample_id`、真实标签、输出键和批次元数据，没有校验 `generated_text`、`parsed_label`、`is_valid`、`parse_error`、`input_tokens`、`generated_tokens` 与 `latency_ms` 的存在性、类型和相互一致性。
- 因此，缺字段或字段被篡改但仍是合法 JSON 的部分行会被视为已完成。`finalize()` 会先原子发布 `predictions.jsonl` 并把进度标为 `finished`，随后 `_summary_from_rows()` 才可能因缺字段失败；若字段齐全但解析结果被改写，最终预测文件还会与重新解析生成文本所得摘要不一致。
- 这不满足“损坏行在模型加载前拒绝”的验收条件。恢复登记时应严格校验完整行模式，并重新解析 `generated_text` 核对解析字段后才能将样本标记为完成。

### 3. SwanLab 的“每批峰值显存”实际是整轮累计峰值

- 位置：`thesis/experiments/llm_probe/src/flow_probe/evaluate_model.py:870`、`thesis/experiments/llm_probe/src/flow_probe/evaluate_model.py:886`、`thesis/experiments/llm_probe/src/flow_probe/evaluate_model.py:624`
- CUDA 峰值统计只在进入批次循环前重置一次，随后每批调用 `max_memory_allocated()`。第二批及之后得到的是从首次重置到当前时刻的累计最高值，而不是当前批次自身的峰值。
- 该累计值通过进度对象以 `memory/gpu_peak_mib` 每批写入 SwanLab，导致较短尾批次或恢复后的批次继承前面批次的高水位，不能用于比较逐批显存或诊断异常批次。
- 应在每批开始前重置峰值统计，同时另行维护整轮最大值供最终摘要使用，并增加能区分“当前批峰值”和“整轮峰值”的测试。

## 验证记录

- 审查范围仅包含实施计划指定的四个文件及其工作树差异。
- 未修改生产代码或测试代码。
- 未重跑全套测试；控制器通报服务器两个目标测试共 54 项通过，但这些理想路径测试未覆盖上述三个故障窗口。

