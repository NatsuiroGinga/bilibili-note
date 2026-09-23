# DRIFT 论文语料候选位置诊断报告

## 检查点

已将工具升级为全量流式候选审计。工具先打开候选角色 Parquet 元数据取得 `num_rows` 和行组边界，再按批读取 `domain,label`；第一遍每个角色只保留容量为 `count` 的最大堆和当前候选域名字典，按 `SHA256(length_prefix(data_revision, corpus_namespace, exact_esld))` 保留哈希最小的唯一候选。第一遍完成后仅对最终候选域名字典再流式核验一遍同一 Parquet，精确统计 `selected_member_raw_rows` 与 `selected_member_duplicate_rows`，并重新严格校验标签。不输出域名、成员或数据副本。

候选规范只允许 `corpus_namespace` 和 `roles` 两个顶层字段。`roles` 必须严格包含 `source_train`、`source_validation`、`target_test`，每个角色条目只含 `role` 与正整数 `count`。`member_seed`、模型、攻击、阈值、样本、路径及未知字段均拒绝。

输出的 `candidate-audit.json` 只包含角色、原始行数、选中数量、候选根、长度/字符统计、行组索引和跨用途聚合；行组索引由 `pyarrow.parquet.ParquetFile.metadata` 规划，记录读取使用 `iter_batches(columns=["domain", "label"])`，不读取其他列。审计不声称全源实体唯一、总体代表性或最终论文规模。

## 范围边界

用途约束为：`source_train` 仅接受 `scope=source` 且 `split∈{train,test}`；`source_validation` 仅接受 `scope=source` 且 `split=val`；`target_test` 仅接受 `scope=target` 且 `split=target`；同一 `role` 不得跨用途。工具拒绝空用途列表、`member_seed`、模型、攻击、阈值、物化和记录列读取。

本工具是论文语料候选的工程诊断，不评价模型、攻击方法或训练效果。跨用途只在各角色候选集合内做交集与标签冲突统计；冲突使审计阻断，同标签重合只披露不删除。

每个角色开始时原子写入 `role-status.json` 的 `running`；第一遍完成后进入 `selected_member_validation` 阶段，再写入 `complete`。两遍均每 30 秒按已读行数、吞吐、候选数量、RSS 和耗时原子写入心跳并输出。外部中止不会覆盖当前角色的 `running` 状态。第二遍只保留最终候选域的计数，不建立全量集合、缓存或临时文件。

运行目录门禁允许启动前目录不存在，或目录只含启动器预创建的普通 `console.log`；其他文件、目录、符号链接和 `.partial` 均拒绝覆盖。工具不创建运行目录本身，由启动器负责创建并定向控制台日志。

## 路径解析修复

首次元数据审计前发现：主流程已通过 `resolve_repo_relative` 将仓库相对候选规范解析为安全绝对路径，解析函数又重复拒绝绝对路径，导致合法候选规范在读取前失败。现已移除重复拒绝；路径边界仍只由 `resolve_repo_relative` 负责。修复命令为编辑 `load_candidate_spec` 删除二次 `is_absolute()` 拒绝。静态验证使用仓库相对路径经合同解析后调用解析函数，未读取 Parquet。

## 静态验收

已执行并通过以下命令，退出码均为 `0`：

- `/opt/miniconda3/envs/rwkv/bin/python -m py_compile thesis/experiments/llm_probe/tools/ch3_drift_paper_corpus_diagnostic.py`
- `/opt/miniconda3/envs/rwkv/bin/python thesis/experiments/llm_probe/tools/ch3_drift_paper_corpus_diagnostic.py --help`
- `PYTHONDONTWRITEBYTECODE=1 /opt/miniconda3/envs/rwkv/bin/python -c 'import importlib.util, sys; ...'`（隔离导入并确认未加载 `torch`、`pyarrow`）
- `git diff --check -- thesis/experiments/llm_probe/tools/ch3_drift_paper_corpus_diagnostic.py .Codex/docs/2026-09-23-DRIFT源期训练抽样合同/paper-corpus-diagnostic-report.md .Codex/docs/2026-09-23-DRIFT源期训练抽样合同/paper-corpus-diagnostic-skill-receipt.json`
