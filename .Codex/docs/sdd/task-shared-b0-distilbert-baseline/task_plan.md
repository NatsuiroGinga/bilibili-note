# 共享 B0 DistilBERT 判别式基线实施计划

> **执行方式**：使用 `subagent-driven-development` 分派实现与独立审查。禁止使用测试驱动开发；先完成实现，再运行覆盖输入合同、指标和恢复状态的最小服务器测试。

## 目标

在不修改 `dataset-v1-shared-b0` 的前提下，使用同一冻结 `sample_id`、字段预算和确定性文本视图完成 DistilBERT 种子 42 判别式二分类基线，为普通 Qwen、树模型、状态监督和标准 PINN 提供同协议深度判别门槛。

## 架构

- 新增独立模块读取 `candidate/bert_train.parquet`、`validation/genis_bert.parquet` 和 `validation/tqhc2_bert.parquet`。
- 使用 `distilbert-base-multilingual-cased` 或服务器上与该标识严格对应的本地镜像；现有文本字段名为中文，禁止换成英语重物化或改用测试集选择模型。
- GeNIS 验证集只负责开发期模型选择；TQH-C2 固定验证集在模型冻结后只评价一次，不参与学习率、轮数、阈值或批量选择。
- 训练、两份评价、运行状态、配置、日志、预测、成本、环境、输入绑定和制品清单保存在唯一运行根目录，并上传 SwanLab 在线项目 `mortiswang/malicious-traffic-llm`。

## 全局约束

- 数据根固定为服务器 `runs/data-frozen/dataset-v1-shared-b0/`，必须核对发布清单、文件大小和 SHA-256，不得读取 `build-a`、`build-b` 或原始数据。
- 输入只允许 `sample_id`、`stable_order`、`text` 和 `label`；训练前拒绝重复样本、乱序、非法标签、空文本、训练与验证重叠以及清单哈希不一致。
- 默认种子 `42`，标签映射固定为 `0=benign`、`1=malicious`；不得依据 TQH 或后续最终测试调整超参数。
- 硬件入口采用 `device=auto`、`precision=auto`。CPU 必须能完成数据合同和最小前向冒烟；正式训练若无可用 GPU，应结构化退出而不是导入崩溃。
- 评价至少报告准确率、宏平均 F1、良性/恶意 F1、恶意召回、良性误报率、平衡准确率、期望校准误差、布里尔分数、吞吐、延迟、训练时间和峰值内存/显存。
- SwanLab 标签均不超过 20 个字符；逐步训练损失、学习率和 GeNIS 开发指标必须在线可见，结束后用云端状态、摘要与已知指标数据点联合验收。
- 所有运行继续标记为 `theory_selection/review_pending`，不得写入论文最终主表。
- 不修改现有 Qwen、HGB/XGBoost、共享视图或冻结数据制品；不提交、不推送 Git。

## 任务一：实现冻结输入、训练与评价入口

**文件范围**

- 新建：`thesis/experiments/llm_probe/src/flow_probe/shared_b0_distilbert_baseline.py`
- 新建：`thesis/experiments/llm_probe/configs/shared_b0_distilbert_seed42_v1.yaml`
- 新建：`thesis/experiments/llm_probe/tests/test_shared_b0_distilbert_baseline.py`
- 可选精准修改：`thesis/experiments/llm_probe/pyproject.toml`，仅增加 `flow-probe-shared-b0-distilbert` 入口；若当前未提交差异使安全修改不可判定，则保留 `python -m` 入口并在报告说明。

**实现要求**

1. 配置解析和启动前检查必须在导入或加载模型权重前完成。
2. 数据加载器按 `stable_order` 验证顺序，保留 `sample_id`，并把标签映射、文件哈希和样本数写入输入绑定。
3. 使用 Hugging Face `AutoTokenizer`、`AutoModelForSequenceClassification` 与可复现训练循环；支持梯度累积、自动精度、检查点和从最新合法检查点恢复。
4. 在 GeNIS 上冻结模型选择后，分别保存 GeNIS 与 TQH 的逐样本概率、预测、真实标签和指标；阈值固定为 `0.5`。
5. 运行状态至少包含 `prepared`、`running`、`interrupted`、`failed`、`finished`，状态和最终制品清单原子写入。
6. SwanLab 每个优化步记录训练损失和学习率，每次开发评价记录完整指标，运行结束明确 `finish`。

**最小服务器验证**

- 只运行本任务测试文件中的直接目标节点，覆盖：真实配置可解析、冻结三文件绑定、泄漏/重叠拒绝、标签映射、指标数值、CPU 小模型或桩前向、状态恢复和 SwanLab 标量结构。
- 对新增 Python 文件集中运行一次 Black；Ruff 只运行一次，若无语法或结构问题不重复。

## 任务二：服务器冒烟与正式种子 42 运行

**文件范围**

- 新建：`thesis/experiments/llm_probe/scripts/run_shared_b0_distilbert.sh`
- 按需更新：`thesis/experiments/llm_probe/scripts/AGENTS.md`，仅在本轮发现并修复新的可复用故障后写入。
- 新建报告：`.Codex/docs/sdd/task-shared-b0-distilbert-baseline/implementation-report.md`

**启动门禁**

1. 使用白名单 `rsync` 精确同步本任务文件，不使用 `--delete`；服务端先 `source ~/.bashrc`，再启用严格 Shell 模式。
2. 重查 GPU、磁盘、`uv`、`rg`、`fd`/`fdfind`、模型路径、冻结输入哈希和依赖；不得用 Shell 别名冒充可执行文件。
3. 先完成 16 条非最终样本冒烟，确认损失有限、概率合法、预测增量落盘、SwanLab 有数据点和恢复状态有效。
4. 冒烟通过后使用唯一目录 `runs/baselines/shared-b0-distilbert-seed42-theory-selection-review-pending-v1/` 在 `screen` 中启动正式运行；检查点间隔不超过 20 个优化步或 10 分钟。
5. 正式结束后核对退出码、状态、两份预测行数、指标、成本、输入绑定、全部制品哈希和 SwanLab 云端图表。

## 任务三：独立审查与写回

1. 新的代码审查代理只审查本任务差异，重点检查数据泄漏、TQH 调参、标签映射、恢复语义、成本口径和 SwanLab 真实性。
2. 严重或重要问题必须最小修复并重跑直接覆盖节点；审查超过 10 分钟时正式运行可标记 `review_pending` 并并行进行。
3. 结果验收后更新 `output/第一创新点实验总控.md`，写明服务器路径、SwanLab 运行号、关键指标、成本、裁决和下一门禁；详细日志只留在本任务报告和唯一运行目录。

## 完成条件

- DistilBERT 在同一冻结候选训练集、GeNIS 开发验证和 TQH 固定外部验证上得到可复核指标。
- 数据、模型、运行、成本与 SwanLab 证据完整，能在服务器重启后恢复或判定完成。
- 独立审查无未处理的严重或重要问题；否则保持 `review_pending`，不将结果晋级为已验收基线。
