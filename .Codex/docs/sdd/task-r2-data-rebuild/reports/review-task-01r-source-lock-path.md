# 任务 01R 源锁路径独立复审

## 结论

任务 01R 的运行时路径修复通过只读复审。未发现严重或重要问题。

生产常量、冻结配置、任务 03 正式移交入口、正式移交参数和两处最小断言均一致指向：

`runs/data-freeze-configs/r2-protocol-v1/source-locks-v1`

任务 03 的有效代码、配置、脚本和正式参数中，没有发现仍把共享父目录 `runs/data-freeze-configs/r2-protocol-v1` 当作源锁根的消费点。

## 发现

### 低：实施计划的两处历史制品说明仍使用旧父目录

- `.Codex/docs/sdd/task-r2-data-rebuild/task_plan.md:91` 的目录树仍把四项源锁直接列在共享父目录下。
- `.Codex/docs/sdd/task-r2-data-rebuild/task_plan.md:421` 的任务 01 制品表仍把四项源锁直接列在共享父目录下。
- `.Codex/docs/sdd/task-r2-data-rebuild/reports/run_r2_source_restore_preflight.sh:45` 是历史复现脚本，仍显式传入共享父目录。

这些位置不属于任务 03 的当前运行时消费链，不影响本轮代码正确性；但后续更新计划时应把前两处改为 `source-locks-v1/`，并明确历史脚本不可作为当前正式入口，避免恢复上下文时误读。

## 核验依据

### 路径一致性

- `src/flow_probe/r2_protocol_contract.py`：`SOURCE_LOCK_ROOT` 指向专属子目录。
- `configs/r2_protocol_data_v1.yaml`：`dataset.source_lock_root` 与生产常量一致。
- `src/flow_probe/r2_protocol_tqhc2.py`：任务 03 的 `expected_paths["source_lock_root"]` 指向专属子目录，并继续从该目录读取三项锁文件及写入移交清单。
- `runs/launchers/r2-protocol-data-rebuild-v0/local-producer/tqhc2-handoff-params.json`：正式参数的 `source_lock_root` 指向同一专属子目录。
- `tests/test_r2_protocol_contract.py`：新增配置路径精确断言。
- `tests/test_r2_protocol_tqhc2.py`：新增正式移交参数路径精确断言。

### 变更边界

以当前 `HEAD` 为基线进行逐文件文本等价比较：

- `r2_protocol_contract.py`、`r2_protocol_data_v1.yaml`、`r2_protocol_tqhc2.py` 除把旧父目录替换为 `source-locks-v1` 外，其他字节一致。
- 两份测试没有删除或改写既有内容，只新增上述两项路径断言。
- 因此本轮没有改变数据、标签、字段、摘要校验、文件集合校验、原子发布或覆盖拒绝逻辑。

### ns-3 冻结制品

- `ns3-config-manifest.jsonl` 的 SHA-256 仍为 `a0efc42ed26c0e4bc2c1622f850f5ee61a20348f29693bafa8008108792be793`。
- `ns3-config-manifest.sha256` 的 SHA-256 仍为 `43bbf0056d66fa6841285a18f426a895d645bd4762908b06e46a98ec4869f5ca`。
- 两项摘要与任务 04 冻结记录一致，未发现移动、改写或删除。

## 已知后续门禁

- 正式参数中的 `project_root` 仍绑定旧隔离工作树。任务 01R 按计划形成新提交并重建执行代码锁后，必须同步生成或更新正式参数，不能直接用当前参数启动任务 03。
- 本复审遵守只读范围，没有运行测试、格式化、静态检查、冒烟实验或正式实验。
