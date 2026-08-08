# 生成式评测断点安全修复记录

**日期：** 2026-07-30

**任务边界：** 只修复生成式评测的部分日志恢复、恢复行校验、最终发布顺序和逐批 CUDA 峰值统计；未修改训练侧、配置、数据或服务器制品。

## 根因

1. `predictions.partial.jsonl` 使用直接追加写入。断电可能留下截断尾行或仅写入部分行的半批次，原恢复逻辑无法区分已提交批次与未提交尾批。
2. 恢复登记只校验记录身份、标签合同和批次元数据，未核对生成文本、解析结果、有效性、错误、令牌数和延迟。`predictions.jsonl` 与 `finished` 又早于汇总生成，合法 JSON 损坏可能在最终文件发布后才触发失败。
3. CUDA 峰值只在批次循环前重置一次，第二批开始读取的是整轮累计高水位；SwanLab 的逐批键因此不代表当前批次。

## 修复内容

- 每行新增 `_journal_batch_size`，记录本批预期行数。
- 每批使用临时 JSONL 文件、`fsync` 和原子替换发布完整部分日志；内存状态只在原子替换成功后更新。
- 恢复时只解析以换行结束的完整行，按连续批号和声明行数识别已提交批次；截断尾行或未完整尾批会被整批丢弃，并原子重写为最后一个完整批次边界。非尾部缺批、批号跳跃和批次元数据冲突继续严格拒绝。
- 恢复、追加和最终发布前统一校验 `generated_text`、`parsed_label`、`is_valid`、`parse_error`、`input_tokens`、`generated_tokens`、`latency_ms` 的存在性与类型，并重新调用严格解析器核对三个解析字段。
- `finalize()` 改为先构造最终行并执行汇总回调。只有汇总成功且摘要成功落盘后，才原子发布 `predictions.jsonl` 并把进度写为 `finished`。
- 每批生成前调用 CUDA 峰值重置；进度同时保留整轮最大值和当前批峰值，SwanLab 的 `memory/gpu_peak_mib` 改为上报当前批峰值。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/evaluate_model.py`
- `thesis/experiments/llm_probe/tests/test_evaluate_model.py`
- `.Codex/docs/sdd/task-generation-runtime-acceleration/fix-report.md`

## 测试与验证

### 红灯证据

- 截断尾批：旧实现在截断 JSON 尾行报“部分预测行损坏”，不能恢复。
- 语义字段：旧实现接受缺少 `generated_text` 的合法 JSON 行。
- 发布顺序：旧 `finalize()` 不接受汇总门禁，并会直接发布最终预测。
- CUDA 峰值：旧实现没有逐批重置辅助入口。
- 不可哈希解析标签：旧实现对列表型 `parsed_label` 抛出未受控 `TypeError`。

以上红灯均通过直接调用精确测试函数取得，未在本机启动 `pytest`。

### 绿灯证据

- 直接调用 `test_evaluate_model.py` 中 37 个无 `torch` 依赖的精确检查，退出码为 `0`。
- 覆盖七个关键语义字段的缺失组合、八个非法类型或语义组合、截断半批恢复、汇总失败不发布、正常恢复发布、逐批峰值重置和 SwanLab 当前批峰值。
- 本机环境缺少 `torch`，旧的批量张量测试由 `pytest.importorskip("torch")` 主动跳过；未以本机结果替代服务器目标测试。

### 格式与静态检查

- Black：按要求集中执行一次，两个 Python 文件均完成格式化，退出码为 `0`。
- Ruff：按要求执行一次，报告一项 `B023`，指出循环内 lambda 未显式绑定 `batch_prompts`。已改为默认参数绑定；根据目录规则未重复运行 Ruff。
- `python -m py_compile src/flow_probe/evaluate_model.py tests/test_evaluate_model.py`：退出码为 `0`。
- `git diff --check`：见最终范围审计结果。

## 未执行与遗留风险

- 未在本机运行 `pytest`。
- 未同步服务器、未启动 GPU 评测、未提交代码。
- 原子重写部分日志会增加 JSONL 写入量；模型推理占主耗时，但仍需服务器小批量吞吐预检确认实际开销。
- 服务器需运行 `test_evaluate_model.py` 与既定目标测试，并在非最终样本上验证批量预测一致性、吞吐和真实逐批峰值。
