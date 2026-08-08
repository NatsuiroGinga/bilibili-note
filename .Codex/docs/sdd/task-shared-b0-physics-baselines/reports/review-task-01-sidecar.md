# 共享 B0 物理旁路任务 01 独立审查报告

## 严重

未发现严重问题。

## 重要

### 1. 独立校验没有把旁路数值、来源归属和掩码重新绑定到冻结来源

**位置：**

- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):1053
- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):1065
- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):943
- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):952
- [test_shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py):247

**影响：** `validate_shared_b0_physics_sidecar` 只重新计算三个来源文件的哈希，并累加 `source_manifest` 自报的记录数；它没有读取来源 JSONL，也没有逐条核对 `sample_id` 所属来源、四窗口字段、队列状态或确定性掩码。输出记录校验只要求数组长度正确、数值有限、掩码至少含一个 `True`。因此，累计接收量与出队量互换、相邻差分错误、`source_split` 错配或掩码改成任意非空布尔数组时，只要同时更新同一输出目录内的清单哈希，独立校验仍可通过。当前正常路径测试也只断言数组长度和首条掩码数量，没有用手算值约束生产变换。

**证据：** 物化器在第 612 至 675 行完成实际变换；校验路径在第 1048 至 1073 行只处理来源清单的路径、哈希和自报计数，在第 935 至 965 行只检查输出形状、有限性和宽松掩码，没有从来源重建期望值。测试第 247 至 255 行同样未核对任一累计数组的相邻差分或状态归一化结果。

**最小修复建议：** 校验时加载已绑定配置和三个来源 JSONL，严格核对每源 807 条及 `sample_id -> source_split` 映射；逐条验证锚点时间、状态归一化、五个累计数组的相邻差分和确定性掩码与来源记录一致。测试至少增加一条手算完整记录，并分别篡改累计量、来源划分和掩码后更新依赖清单哈希，确认失败原因来自语义门禁而不是外层文件哈希。

### 2. `anchor0_plus_one` 掩码由含场景语义的 `group_id` 派生，形成场景代理变量

**位置：**

- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):559
- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):566
- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):572
- [test_shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py):52
- [implementation-input.md](/Users/bilibili/personal/note/.Codex/docs/sdd/task-shared-b0-physics-baselines/implementation-input.md):30

**影响：** 代码按 `group_id` 的哈希排名决定第二个可见锚点，同组记录共享同一掩码。测试夹具明确把 `scenario-*` 写入 `group_id`，说明掩码模式可能成为场景身份的四值代理变量。即使代码没有直接读取标签或提示词，下游看到 `state_mask_inputs` 后仍可能利用该相关性，造成场景泄漏或场景相关的监督偏差，削弱两条物理基线比较的解释力。

**证据：** 第 559 至 578 行从 `group_id` 构造排名，再以 `rank % 4` 选择第二锚点；第 52 行夹具的 `group_id` 含场景名。当前测试只确认首条记录有两个 `True`，没有验证掩码对场景、标签、提示词和来源划分保持不变。

**最小修复建议：** 用不含场景语义的冻结 `sample_id` 与种子 42 独立派生第二锚点，禁止使用 `group_id`、标签、提示词、场景名或来源划分。增加不变性测试：保持 `sample_id` 不变并改变 `group_id`、提示词、完成标签和来源顺序后，掩码必须不变；每条掩码必须严格为锚点 0 加一个其他锚点。

### 3. 三个冻结来源的逐源 807 条、路径和哈希没有形成不可绕过的生产配置门禁

**位置：**

- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):367
- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):386
- [test_shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py):204
- [test_shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py):218
- [shared_b0_physics_sidecar_v1.yaml](/Users/bilibili/personal/note/thesis/experiments/llm_probe/configs/shared_b0_physics_sidecar_v1.yaml):19

**影响：** 配置加载器允许任意项目内来源路径、任意匹配哈希和任意非负逐源计数，只要求三个计数之和为 2,421。因此 `1/1/2419` 等划分可以通过加载门禁。真实生产配置测试虽然直接加载 YAML，但只断言三个计数当前为 `807/807/807`，没有固定三个逻辑路径和三个 SHA-256；把生产 YAML 改指另一组三文件并同步哈希后，测试仍可通过。冻结来源身份因此依赖人工检查，而不是可执行合同。

**证据：** 第 367 至 380 行直接接受配置给出的路径、哈希和计数；第 386 行只校验总和。真实配置测试第 212 至 218 行未断言任何来源路径或哈希，也未断言三个来源划分标识。

**最小修复建议：** 加载器明确要求三个 `expected_count` 均为 807；真实配置测试逐项固定 `split/path/sha256/expected_count` 四元组，并固定掩码种子、阶段和状态。独立校验还应解析该真实配置，将 `source_manifest` 的三项来源逐字段与配置比较，而不是只验证配置文件自身哈希。

### 4. 预建空输出目录在发布替换失败时会被删除且无法恢复

**位置：**

- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):707
- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):867
- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):871
- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):872
- [test_shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py):383

**影响：** 对调用方已经创建的空目录，代码先执行 `rmdir()`，再执行 `.partial -> output` 替换。如果替换因权限变化、并发占用或文件系统错误失败，异常清理只删除 `.partial`，不会恢复原空目录。这违反“失败清理安全”和“不覆盖既有冻结制品”的要求，并对调用方路径产生破坏性副作用。

**证据：** 第 867 至 871 行在两个独立操作之间留下失败窗口；第 872 至 875 行只清理 `partial`。双物化测试只覆盖替换成功的预建空目录，没有注入替换失败，也没有断言失败后原目录仍存在。

**最小修复建议：** 优先使用能够直接替换空目录的单次原子重命名；若需兼容不支持该行为的平台，则使用可恢复的同级占位或备份协议，并在任何发布失败后恢复原空目录。增加替换失败注入测试，断言原空目录保留、`.partial` 被清理且既有文件绝不被覆盖。

### 5. 最终制品集合和符号链接未受校验，双物化测试也不拒绝未登记文件

**位置：**

- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):977
- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):980
- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):1119
- [test_shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py):389

**影响：** 校验器只确认五个必要路径是文件；`Path.is_file()` 会跟随符号链接，并且代码没有枚举和拒绝额外文件。分类副本检查也只覆盖两个固定名称。因而输出中可以存在指向外部内容的必要制品、改名后的分类副本或任意未登记文件，仍返回 `passed`。双物化测试只是比较两次目录中的文件集合彼此相等；如果两次都稳定地产生同一个未登记文件，测试仍会通过。

**证据：** 第 977 至 983 行没有执行精确文件集或符号链接检查；第 1119 至 1127 行只核验四个非自引用制品的登记哈希，且没有验证 `required_files` 的精确内容。测试第 389 至 396 行未把实际集合与 `REQUIRED_OUTPUT_FILES` 比较。

**最小修复建议：** 使用不跟随链接的文件状态检查，拒绝输出根及其所有后代符号链接；递归枚举最终普通文件并要求集合严格等于 `REQUIRED_OUTPUT_FILES`；校验 `materialization_audit.required_files` 与该集合完全相等。增加额外文件、改名分类副本、必要文件符号链接、非空目录和遗留 `.partial` 的失败测试。

## 建议

### 1. 增加物理量取值域门禁

**位置：** [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):515

当前只检查有限数，负的队列字节、接收字节、包数、出队字节和丢弃字节仍可进入旁路，包数也可为小数。建议按字段语义拒绝负值，并要求包计数为非负整数；为每类非法值增加最小失败测试。

### 2. 固定阶段、状态和记录模式版本

**位置：**

- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):402
- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):912

加载器目前接受任意非空 `stage/status`，输出记录校验也不检查 `schema_version`。建议把本任务固定为 `theory_selection/review_pending`，并要求每条记录的模式版本精确匹配，同时拒绝未声明的额外字段，避免错误制品被标成冻结或跨版本混用。

### 3. 让解析内容与哈希来自同一字节快照

**位置：**

- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):310
- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):399
- [shared_b0_physics_sidecar.py](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py):422

配置先解析、后另行打开计算哈希；分类文件和来源文件也分别执行哈希与解析。建议一次读取原始字节，同时由该字节计算 SHA-256 并解析内容，物化完成后再独立重读哈希。这样可避免并发替换时“用于计算的内容”和“清单绑定的字节”不是同一快照。

## 审查结论

- 结论：**请求修改**。
- 发现统计：严重 0 项，重要 5 项，建议 3 项。
- 当前实现的正常生成路径具备只按 `sample_id` 排序连接、分类文件只读、相对路径清单、无时间戳序列化和五锚点累计量的基本结构。
- 由于独立语义校验、掩码防泄漏、冻结来源硬绑定、失败恢复和精确制品集合仍有重要缺口，现有服务器目标测试即使通过，也不足以完成任务 01 放行。

## 未执行与服务器风险

- 按审查简报要求，本轮未运行本机 `pytest`、格式化、静态检查、服务器命令或网络操作。
- 实现报告说明本机缺少冻结分类 JSONL，因此本轮无法核验生产分类集合、真实三源字段和值域；修复后仍需在服务器 `uv` 环境运行目标测试和真实配置端到端物化。
- 服务器验证还需确认 `PyYAML` 可导入、三个生产来源逐项 SHA-256 与配置一致、每源恰为 807 条、实际字段名与四窗口假设一致，以及相邻差分能够逐字段还原来源记录。
