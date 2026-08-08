# 统一预算生成器独立代码审查

## 修复后复审结论（当前）

**请求修改，暂不允许启动真实 `build-a`/`build-b`。**

- 严重问题：1 项。
- 重要问题：1 项。
- 建议：3 项。
- 此前 7 项重要问题中，第 1、3、4、5、6 项已消除；第 2 项仍有一个恢复缺口；第 7 项已由代码风险转为必须通过真实双构建裁决的运行风险。

### 严重：校验和清单登记了发布前被删除的状态文件

位置：`src/flow_probe/unified_budget.py:1398-1405`，`src/flow_probe/unified_budget.py:1545-1562`，`src/flow_probe/unified_budget.py:1579-1594`。

生成 `budget_checksums.json` 时，递归枚举只排除了 `_INCOMPLETE`、校验和文件和冻结清单，仍会把 `materialization_state.json` 纳入 `artifacts`。随后实现先把状态从 `running` 改写为 `finished`，再删除状态文件并发布目录。最终结果因此必然包含一个指向不存在文件的校验和条目，其哈希还对应删除前的旧状态，`artifact_count` 也多计一项。

该问题会使每一次成功物化的冻结清单失效。两个构建会以相同方式产生相同错误，因此逐字节一致仍会通过，不能作为正式验收依据。

最小修复：明确从 `checksum_paths` 排除 `materialization_state.json`；写完冻结清单后、删除临时状态前，按 `budget_checksums.json` 逐项验证路径存在、大小和 SHA-256，并断言登记路径集合等于最终应发布制品集合。新增测试必须读取校验和文件并逐项复验。

### 重要：`.partial` 状态仍在全部大规模内存计算之后才建立

位置：`src/flow_probe/unified_budget.py:830-841`，`src/flow_probe/unified_budget.py:949-1207`，`src/flow_probe/unified_budget.py:1284-1368`，`src/flow_probe/unified_budget.py:1392-1409`。

当前 `try`、`.partial`、`_INCOMPLETE` 和状态文件直到协议全部加载、1,179,168 条开放集完成分层选择、跨源身份检查完成且 1,410,346 行主索引已构造后才出现。真实规模下最耗时、最占内存的阶段发生异常或实例关机时，仍不会留下 `prepared/running/failed/interrupted` 状态。现有测试只在 `to_parquet` 阶段注入异常，未覆盖这一窗口。

最小修复：完成输出白名单与配置基础校验后立即创建 `.partial` 和 `prepared` 状态；输入哈希逐项验证后原子更新状态，再进入协议加载、选择和主索引构造。把这些阶段纳入同一异常状态处理范围，并增加协议加载或选择阶段失败测试。

### 前次问题复核

- 第 1 项已消除：预算和元数据写入 `manifests/budgets/`，测试核对完整相对路径集合。
- 第 2 项部分消除：普通异常与 `BaseException` 会保留失败现场，但保护范围开始过晚。
- 第 3 项已消除：比较训练与开放集 `group_id`，并拒绝开放集训练来源分区；新增不同标识同会话测试。
- 第 4 项已消除：开放集预算从源记录派生 `source_split`，并与主索引逐行核对。
- 第 5 项已消除：输出仅接受项目根内配置声明的独立构建目录。
- 第 6 项已消除原阻塞项：主要算法标识、字段列表、会话与 UTC 合同、清单划分、组数、联合分层数和公开检测 Hamilton 配额均已执行门禁。
- 第 7 项可通过真实双构建关闭：已删除未使用的百万项字典、复用索引并降低身份检查占用；剩余逐行 `.loc` 和主索引峰值应由真实输入测量裁决。

### 真实双构建验收

修复当前严重和重要问题并通过直接回归后，可先运行 `build-a`，成功且资源可接受后再运行 `build-b`：

- 两次分别记录命令、配置/实现/输入 SHA-256、阶段状态、墙钟耗时、峰值常驻内存、磁盘增量和退出状态。
- 核对主索引 1,410,346 行及七份预算的固定计数、顺序、候选子集和 ns-3 全量一次。
- 对每份校验和清单逐项验证文件存在、大小和 SHA-256，再验证冻结清单绑定的校验和文件哈希。
- 比较两个目录的相对文件集合、文件大小和 SHA-256；全部一致才满足逐字节确定性。
- `build-a` 若内存不足、耗时不可接受或磁盘不足，先裁决资源路径，不直接启动 `build-b`。

满足以上条件后，可关闭真实规模风险；仅有合成测试的双目录一致性不能关闭。

### 当前建议

1. 显式校验 `source_dataset`、`outputs.dataset_root` 与 `publication.publish_target` 一致性、双构建与独立审查布尔门禁、两个构建名唯一、ns-3 选择算法和 `outputs.required_record_fields`。
2. 使用 `pd.isna()` 拒绝 GeNIS/TQH-C2 缺失分层值，并统一拒绝或规范化 ns-3 首尾空白标识。
3. Black 已通过；Ruff 仅剩生产文件和测试文件各一个导入顺序问题，交付前由实现代理处理。

### 当前验证

- `pyproject.toml:64` 的入口仍正确指向 `flow_probe.unified_budget:main`。
- 本地 Black 与限定任务文件的 `git diff --check` 通过；Ruff 仅报告 2 个导入顺序问题，无语法或结构错误。
- 只读核对服务器真实 TQH-C2 `samples.parquet`，确认包含新实现要求的 `split_id` 字段。
- 本轮未运行模型、未提交 Git、未修改生产代码或测试，也未查看其他工作树差异。

## 初审记录（历史）

**请求修改，当前不得启动真实统一预算物化或发布。**

- 严重问题：0 项。
- 重要问题：7 项。
- 建议：3 项。
- 审查范围仅限 `src/flow_probe/unified_budget.py`、`tests/test_unified_budget.py`、`pyproject.toml` 的新增入口、`configs/unified_budget_v1.yaml` 及指定服务器验证日志。
- `pyproject.toml:64` 的控制台入口指向 `flow_probe.unified_budget:main`，入口注册本身未发现问题。

## 重要问题

### 1. 预算清单未写入真实配置声明的目录，正式物化布局无效

位置：`configs/unified_budget_v1.yaml:224-228`，`src/flow_probe/unified_budget.py:1110-1117`，`src/flow_probe/unified_budget.py:1131-1297`，`tests/test_unified_budget.py:487-500`。

真实配置声明 `outputs.budgets_dir: manifests/budgets`，但实现只校验一组裸文件名，并把主索引、七份预算清单和三份元数据全部直接写到 `output_dir`。测试还明确把这一平铺布局固化为期望。下游按固定配置寻找 `manifests/budgets/*.jsonl` 时无法读取结果，因此即使内容哈希正确，该目录也不符合受控数据集合同。

最小修复：解析并校验 `outputs.budgets_dir`，只把 `master_records.parquet` 放在数据集根目录，按合同把预算及其元数据放入安全的项目相对子目录；校验和使用相对数据集根的路径作为键，并增加真实目录结构断言。

### 2. 普通异常会删除 `.partial`，且不同中断类型产生不一致的不可恢复状态

位置：`src/flow_probe/unified_budget.py:1124-1129`，`src/flow_probe/unified_budget.py:1297-1301`。

实现对普通 `Exception` 递归删除整个 `.partial`，违反本实验目录“未完成物化保留独立 `.partial`”的重启恢复与取证合同。另一方面，`KeyboardInterrupt`、进程终止或断电不属于该异常分支，会留下没有阶段或状态文件的 `.partial`，下一次运行只会拒绝覆盖，无法判断可续跑、可校验还是应标记失败。成功结果本身不因此失真，但按量服务器中断后的证据、恢复来源和失败诊断会丢失或阻塞。

最小修复：不要删除失败目录；在写入任何大型制品前原子写入 `prepared/running` 状态，捕获可处理异常后写入 `failed/interrupted`，成功校验后写入 `finished` 再原子发布。重启时只读核验现有 `.partial` 的配置、输入和实现哈希，禁止无依据复用。

### 3. 训练集与开放集只检查样本标识交集，未阻止会话级泄漏

位置：`src/flow_probe/unified_budget.py:799-803`，`src/flow_probe/unified_budget.py:809-817`，`tests/test_unified_budget.py:591-618`。

当前门禁只计算两个清单的 `sample_id` 交集。两个不同 `sample_id` 只要共享同一个 `group_id`/会话，就能分别进入训练池与开放集而不报错；现有测试也只把开放集某一行替换为完全相同的训练样本标识。既有冻结协议加载器只禁止同一套件中的样本跨划分，而 GeNIS 正式训练与开放集使用不同套件，不能替代本模块的跨套件会话门禁。这会直接污染开放集评价并使相关实验结果无效。

最小修复：从已绑定的 `samples.parquet` 提取两个清单对应的 `group_id` 集合并拒绝交集，同时确认开放集行不属于训练来源分区；新增“标识不同但 `group_id` 相同”的回归测试。

### 4. 开放集预算的 `source_split` 被统一硬写为 `test`，与主索引来源语义不一致

位置：`src/flow_probe/unified_budget.py:566-592`，`src/flow_probe/unified_budget.py:1140-1141`，`src/flow_probe/unified_budget.py:1188-1204`，`configs/unified_budget_v1.yaml:47-50`。

主索引的 GeNIS `source_split` 来自每条源记录的 `source_partition`，开放集预算却为全部样本硬写 `test`。因此同一 `sample_id` 在主索引与预算清单中可能具有不同的 `source_split`；实现也未消费 `rewrite_source_roles: false`。若 `test` 想表达预算清单的逻辑划分，它不应覆盖名为 `source_split` 的来源字段。该不一致会破坏来源审计与后续防泄漏检查。

最小修复：预算行的 `source_split` 从主索引对应记录派生；如还需保留清单的 `split_id=test`，使用独立字段表示，并增加逐行核对预算与主索引来源字段一致性的测试。

### 5. `output_dir` 未绑定项目根和发布白名单，允许绕过固定发布路径

位置：`src/flow_probe/unified_budget.py:744-750`，`src/flow_probe/unified_budget.py:1119-1129`，`configs/unified_budget_v1.yaml:247-256`，`tests/test_unified_budget.py:470-485`。

来源路径经过项目根逃逸检查，但输出路径只做 `resolve()` 和“目标不存在”检查。调用方可以把完整受控制品写到项目根外任意可写位置，也可以绕过 `publication.build_root`、`independent_builds` 和 `publish_target`；现有双构建测试正把两个输出放在 `project_root` 外。冻结清单不记录输出位置，生成后无法判断它是否走过合同规定的双构建与发布路径。

最小修复：要求输出位于解析后的 `project_root` 内，并只允许配置声明的独立构建目录；正式 `publish_target` 应由完成双目录逐字节比较的发布步骤占用，而不是由单次构建直接写入。增加绝对路径、`..`、符号链接逃逸和非白名单目录测试。

### 6. 多个真实配置硬门禁仅被记录而未被实现消费

位置：`src/flow_probe/unified_budget.py:686-734`，`src/flow_probe/unified_budget.py:819-939`，`configs/unified_budget_v1.yaml:53-132`，`tests/test_unified_budget.py:24-50`。

实现会使用种子、分隔符和命名空间，但不校验 `quota_algorithm`、`unified_order_algorithm`、`rank_key_fields`、会话连接字段、UTC 时间字段、GeNIS 期望会话数与联合分层数、TQH-C2 期望分配组数与联合分层数、正式清单算法以及候选公开 Hamilton 分配依据。真实配置测试只断言若干 YAML 值存在，不能证明生产解析器执行这些门禁。修改这些声明而保持其余计数自洽时，生成器仍会产出并用该配置哈希签名，造成“配置声称的协议”与“实际执行算法”不一致。

最小修复：对本版本只接受合同规定的算法标识和字段列表；在选择前核对真实组数、联合分层数、清单 `split_id` 与候选源配额的 Hamilton 推导结果。每类关键字段至少增加一个负向测试，证明篡改会被拒绝。

### 7. 真实 141 万条路径存在明显峰值内存与运行时间风险，现有验证未覆盖

位置：`src/flow_probe/unified_budget.py:383-400`，`src/flow_probe/unified_budget.py:880-916`，`src/flow_probe/unified_budget.py:1020-1034`，`src/flow_probe/unified_budget.py:1070-1097`。

`_genis_strata` 每次复制完整索引，并为每个样本额外构造一个最终未使用的 `attributes` 字典；该函数对正式、候选和 1,179,168 条开放集分别执行。随后又建立 1,410,346 项的全局身份字典和 13 列主索引。服务器日志只运行了小型合成夹具与真实 YAML 合同节点，没有执行真实物化、峰值内存或耗时测量，因此当前证据不足以确认该路径能在按量服务器上完成并留下可恢复状态。

最小修复：删除未使用的 `attributes`，只构建一次必要索引并复用，优先用向量化连接和分组替代逐条 `.loc`；身份检查和 JSONL 输出采用可控的流式处理。正式启动前用真实固定输入执行只读规划或完整物化基准，记录峰值常驻内存、阶段耗时和磁盘增量。

## 建议

### 1. 严格拒绝缺失分层值

位置：`src/flow_probe/unified_budget.py:388-396`，`src/flow_probe/unified_budget.py:501-506`。

当前先调用 `str()` 再检查空字符串，`NaN` 和 `pd.NA` 会分别变成 `nan` 与 `<NA>` 并作为合法分层值。建议先使用 `pd.isna()`，再做非空字符串校验。

### 2. 统一 ns-3 标识规范化

位置：`src/flow_probe/unified_budget.py:979-986`，`src/flow_probe/unified_budget.py:623-629`。

加载门禁把 `sample_id` 去除首尾空白后用于预算和唯一性检查，主索引却写入原始值。建议拒绝非规范原值或统一保存规范值，避免预算引用不到主索引记录。

### 3. 补充独立进程与命令入口验证

位置：`tests/test_unified_budget.py:467-555`，`pyproject.toml:64`。

双目录测试证明同一进程、同一小夹具下逐字节一致，但没有覆盖安装后的控制台入口、两个独立进程或真实规模 Parquet。建议在修复阻塞项后增加命令入口冒烟，并让两个独立构建进程比较全部相对路径、大小和 SHA-256。

## 已核验行为

- 候选协议显式传入版本、状态和阶段：`src/flow_probe/unified_budget.py:303-308`。
- 协议、样本和所用清单均有外部哈希与冻结协议内绑定：`src/flow_probe/unified_budget.py:296-310`、`src/flow_probe/unified_budget.py:340-363`。
- Hamilton 当前实现满足现有“最小一条后按剩余容量分配”的测试合同：`src/flow_probe/unified_budget.py:187-232`。
- GeNIS 使用 UTC 自然日并按会话轮转：`src/flow_probe/unified_budget.py:235-263`、`src/flow_probe/unified_budget.py:403-448`。
- TQH-C2 正式清单保持原顺序，候选按配置字段分层抽取；ns-3 按 `train/validation/test` 全量一次；候选均从正式集合产生。
- 主索引只保存引用、角色、视图掩码和源标签审计字段，未复制高维特征。
- JSONL 使用规范键排序和结尾换行；校验和与冻结清单避免自引用；已检查代码中没有凭据、运行时钟、随机标识或绝对输出路径写入成功制品。

## 验证证据

- 服务器目录：`runs/verification/unified-budget-v1-minimal-20260729/`。
- 首次最小套件：`7 passed, 1 failed`；失败原因为泄漏测试夹具漏更新外部清单哈希，生产代码先拒绝哈希不一致，行为正确。
- 夹具修正后的精确泄漏节点：`1 passed`。
- 真实受控配置合同节点：`1 passed`。
- 服务器日志绑定的生产实现、入口和配置 SHA-256 与本次审查文件一致；测试文件在夹具修正后发生预期变化。
- 报告已通过 Prettier 格式化；限定到本任务文件与本报告的 `git diff --check` 通过。
- 本地 `black --check` 显示生产文件和测试文件均需格式化；Ruff 报告 2 个导入顺序和 3 个超长行问题，未发现语法或结构错误。按只审查不修改边界未改动这些文件。
- 未运行模型、未提交 Git，也未查看或评论其他工作树差异。

## 审查裁决

先修复重要问题 1 至 6 并补直接回归，再对真实 141 万条输入执行带资源记录的物化验证。重要问题 7 没有真实规模证据前，不应把小夹具通过解释为正式物化门禁已满足。
