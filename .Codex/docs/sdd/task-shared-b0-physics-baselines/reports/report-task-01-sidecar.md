# 共享 B0 物理基线任务 01 实现报告

## 状态

- 实现状态：完成，等待服务器目标测试。
- 基准提交：`acdf98ba5cc776f7c19495fc53b1164e916eb33c`。
- 任务边界：只实现物理旁路配置、确定性物化、独立校验和行为测试；未修改训练器、冻结数据或运行制品。

## 修改文件

本任务只新增以下四个白名单文件：

- `thesis/experiments/llm_probe/configs/shared_b0_physics_sidecar_v1.yaml`
- `thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py`
- `thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py`
- `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/report-task-01-sidecar.md`

未修改其他文件，未提交、未推送、未连接服务器或公网。

## 公开接口

实现以下三个公开接口：

```python
load_shared_b0_physics_sidecar_config(path: Path) -> SharedB0PhysicsSidecarConfig
materialize_shared_b0_physics_sidecar(
    config: SharedB0PhysicsSidecarConfig,
    output_root: Path,
) -> PhysicsSidecarManifest
validate_shared_b0_physics_sidecar(
    output_root: Path,
    classification_manifest: Path,
) -> PhysicsSidecarAudit
```

异常统一使用 `SharedB0PhysicsSidecarError`，配置、来源、连接或制品任一门禁失败即终止。

## 实现内容

- 分类清单只读绑定 `runs/data-frozen/dataset-v1-shared-b0/candidate/qwen_train.jsonl`。
- 三个 ns-3 来源分别绑定 `train`、`validation`、`test` 文件的逻辑路径、807 条计数和 SHA-256，总数严格为 2,421。
- 只通过 `sample_id` 建立来源记录与分类记录的连接；输出顺序采用分类清单中的全局 `stable_order`。
- 分类清单中的 ns-3 集合由冻结 `sample_id` 前缀 `ns3-h4-` 识别，再与三个 ns-3 来源集合执行双向相等检查。
- 状态掩码固定为 `anchor0_plus_one`、种子 42，并按 `group_id` 的确定性哈希排名生成；连接仍不使用 `group_id`。
- 四个连续窗口转换为五个时间锚点。状态目标使用正的公共容量尺度归一化；容量、接收字节、接收包数、出队字节和两类丢弃字节之和转换为从零开始的五锚点累计量。
- 每条记录写入 `usage=train_fit_diagnostic`、来源划分、来源记录标识和来源 JSONL 文件哈希。
- 输出使用固定 UTF-8、排序键、LF 行尾且不嵌入时间戳或绝对路径；允许传入尚不存在或已经存在但为空的输出根，严格拒绝符号链接、普通文件和非空目录，随后写同级 `.partial` 目录并在独立校验后原子发布。
- 输出包含 `candidate/ns3_physics_train.jsonl`、`dataset_manifest.json`、`source_manifest.json`、`join_audit.json` 和 `materialization_audit.json`。
- 清单哈希采用无自引用顺序：记录、来源与连接审计先写，数据清单再绑定前三者，物化审计最后绑定此前四项。
- 物化前后重新计算分类文件 SHA-256；输出中不复制分类文件，也拒绝分类记录或提示词已有物理旁路字段。
- 独立校验会重新检查分类哈希、配置哈希、三个来源哈希、全部制品哈希、2,421 条计数、唯一标识、集合相等、全局顺序、五锚点长度、严格递增时间、有限数、正尺度和用途。

## 测试覆盖

`tests/test_shared_b0_physics_sidecar.py` 使用 3 个各 807 条、合计 2,421 条的同规模夹具。分类顺序与来源顺序相反，并插入两个非 ns-3 分类记录，以排除按行位置连接的错误实现。

覆盖以下行为：

- 生产配置的固定路径、计数、用途、掩码和来源计数。
- 正常物化、2,421 条计数、唯一性、五锚点字段及独立校验。
- 按 `sample_id` 正确连接并保留分类全局 `stable_order`。
- 分类清单缺失 ns-3 标识。
- 分类清单重复标识。
- 来源重复标识。
- 来源额外标识及集合错配。
- 非递增锚点时间。
- 非有限物理数值。
- 非正归一化尺度。
- 非 `train_fit_diagnostic` 用途。
- 配置加载后来源哈希变化。
- 两个预先创建的独立空输出目录中，全部最终文件逐字节一致。
- 物化前后分类清单哈希不变，且输出不含分类文件副本。

## 验证情况

已执行的只读或静态检查：

- Python 抽象语法树解析：`AST_PARSE_OK 2`，覆盖生产模块和测试模块。
- Ruby YAML 解析：`YAML_PARSE_OK flow_probe_shared_b0_physics_sidecar_config_v1`。
- 三个本机 ns-3 来源的 SHA-256 均与生产配置逐项一致：
  - `train.jsonl`：`d6a6ca23a985223401e1d650d619c2a50b255d2066769e2478cef72cc6239fa0`
  - `validation.jsonl`：`0bbbb4ea483867561c329c896cb4e7745a102cb90024c464654e0b7d673c8723`
  - `test.jsonl`：`6e64d2ab290813a246ed8efcefd1bb19f1026c2de7b7904d111af67b4465ef94`
- 绝对路径字面量审计未发现生产配置或生产模块写入本机、服务器绝对路径。

系统 Python 缺少 `PyYAML`，一次纯 YAML 解析尝试因 `ModuleNotFoundError: No module named 'yaml'` 未执行；随后使用系统 Ruby 对同一文件完成 YAML 语法解析。该失败未触发代码修改。

按任务简报要求，以下操作均未执行：

- 未在本机运行 `pytest` 或任何 Python 行为测试。
- 未运行 Black、Prettier、Ruff、`git diff --check` 或其他格式类检查。
- 未在本机正式物化生产旁路。
- 未连接服务器执行测试或物化。

待服务器执行的精确测试命令：

```bash
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest -q tests/test_shared_b0_physics_sidecar.py
```

## 输入假设

- 冻结分类文件保持共享 B0 发布器合同：每行含唯一 `sample_id`、与行序一致的整数 `stable_order` 和字符串 `prompt`。
- ns-3 分类标识继续使用冻结前缀 `ns3-h4-`；配置把该前缀作为数据合同固定值，而不是使用标签、场景名或提示词识别来源。
- 三个冻结 ns-3 文件各 807 条且总计 2,421 条；每条记录的 `split` 与来源文件登记一致。
- 每条 ns-3 记录包含四个连续窗口、五个队列边界状态、严格为正且与配置容量积分一致的归一化尺度，以及残差所需的接收、出队和两类丢弃量。
- 原始 `test` 或 `validation` 只作为来源划分溯源字段；2,421 条 shared B0 候选当前全部用于 `train_fit_diagnostic`，不得据此声明外部测试或跨拓扑泛化。

## 遗留风险

- 本机没有 `runs/data-frozen/dataset-v1-shared-b0/candidate/qwen_train.jsonl`，因此尚未对生产分类清单执行端到端物化；服务器目标测试和实际物化仍是放行门禁。
- 本任务没有实现训练器。后续消费者必须对五锚点累计容量和通量取相邻差分，恢复四个窗口量后再调用既有队列平衡残差函数。
- 当前物理数据只支持训练拟合诊断。没有新增不相交场景或拓扑，不能产生外部物理泛化结论。
- 用户取消了本轮格式化；独立审查或后续提交前如恢复格式门禁，应只对本任务三个代码、测试和配置文件集中执行一次。

## 白名单审计

- 四个白名单路径均为新增文件。
- 白名单外的现有工作树变更未读取后覆盖、未暂存、未回滚。
- 未生成 `runs/**`、缓存、临时测试制品或分类副本。
- 未执行提交、推送、同步、服务器命令或联网操作。
