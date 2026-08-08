# 共享预算 B0 派生视图实施计划

> **执行要求：** 本任务已由主代理通过子代理驱动开发分派；禁止改写 `dataset-v1`，禁止在本机运行 `pytest`。

**目标：** 从已发布的三源统一预算派生可供 Qwen、BERT 和物理方法共同使用的确定性 B0 视图，同时保持候选清单顺序、来源配额和输入无泄漏。

**实现结构：** 单一物化入口只读取统一主索引、预算清单和三源已冻结制品。公共观测统一为八个数值字段与八个缺失掩码；标签只写入监督目标，禁止进入模型输入。输出先写入 `.partial` 目录，全部计数、哈希与泄漏检查通过后原子发布，已有目标一律拒绝覆盖。

**技术栈：** Python 3.10、pandas、pyarrow、PyYAML、JSONL。

## 全局约束

- 候选样本必须恰为 10,000 条，顺序与统一预算完全一致，来源数固定为 GeNIS 3,973、TQH-C2 3,606、ns-3 2,421。
- 公共字段固定为包数、总字节、包长均值/最小/最大、平均到达间隔毫秒、包速率、字节速率及逐字段缺失掩码。
- GeNIS 直接映射；TQH-C2 仅做显式单位换算；ns-3 只聚合四窗口可观测包数、字节数和窗口跨度，不可观测的包长最小/最大与到达间隔必须保留为空并置缺失掩码。
- 模型输入不得包含标签、来源提示、场景、拓扑、地址、端口、路径、采集单元或物理真值。
- 派生制品必须绑定统一主索引、候选预算、源样本或源序列清单的 SHA-256。

## 任务 1：配置与输入门禁

**文件：**
- 新建：`thesis/experiments/llm_probe/configs/shared_b0_view_v1.yaml`
- 新建：`thesis/experiments/llm_probe/src/flow_probe/shared_b0_view.py`

- [ ] 定义项目相对路径、预期 SHA-256、候选/验证配额和固定字段映射。
- [ ] 验证统一主索引与预算清单哈希、清单字段、稳定顺序、唯一主键和来源配额。
- [ ] 验证三源制品哈希并只加载清单所需样本。

## 任务 2：公共观测映射与视图输出

**文件：**
- 修改：`thesis/experiments/llm_probe/src/flow_probe/shared_b0_view.py`

- [ ] 实现 GeNIS 直接映射与既有缺失掩码复核。
- [ ] 实现 TQH-C2 的微秒到毫秒、微秒到秒换算及零时长速率缺失处理。
- [ ] 实现 ns-3 四窗口包数、字节数、均长和速率聚合；不可观测字段不填充。
- [ ] 按候选清单原顺序生成公共特征、Qwen JSONL、BERT Parquet 和 ns-3 独立物理监督视图。
- [ ] 从既有 GeNIS 与 TQH-C2 验证清单生成互相隔离的验证视图，禁止混入候选训练清单。
- [ ] 生成统计、输入绑定、制品哈希和发布清单，通过检查后原子发布。

## 任务 3：行为测试与命令入口

**文件：**
- 新建：`thesis/experiments/llm_probe/tests/test_shared_b0_view.py`
- 修改：`thesis/experiments/llm_probe/pyproject.toml`

- [ ] 覆盖三源映射、缺失值、TQH 单位换算、ns-3 禁止补造、候选顺序与来源数。
- [ ] 覆盖输入泄漏字段扫描、哈希失配、重复样本、已有输出拒绝覆盖和 `.partial` 原子发布。
- [ ] 注册 `flow-probe-build-shared-b0-view` 命令入口。
- [ ] 本机只运行 Black、Ruff 与 `py_compile`；`pytest` 由服务器执行。

## 验收制品

- 派生目录：`runs/data-frozen/dataset-v1-shared-b0/`
- 候选公共特征：`candidate/common_features.parquet`
- Qwen 候选：`candidate/qwen_train.jsonl`
- BERT 候选：`candidate/bert_train.parquet`
- 分源验证：`validation/genis.*`、`validation/tqhc2.*`
- ns-3 物理视图：`physics/ns3_candidate.jsonl`
- 审计：`manifests/input_binding.json`、`manifests/statistics.json`、`manifests/checksums.json`、`manifests/freeze_manifest.json`

## 状态

- [x] 已读取现有统一预算、训练入口和三源字段契约。
- [ ] 实现与静态验证进行中。
- [ ] 服务器最小测试与真实物化待主代理执行。
