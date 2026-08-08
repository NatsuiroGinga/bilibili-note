# 共享 B0 DistilBERT 基线任务一实现报告

日期：2026-07-30

## 状态

任务一的本地实现已完成。尚未下载模型、同步服务器、启动训练或运行 `pytest`。当前结果只通过本机无数据、无模型的语法与静态检查，必须经过服务器最小目标测试和独立审查后才能启动正式运行。

## 修改文件

- 新建 `thesis/experiments/llm_probe/src/flow_probe/shared_b0_distilbert_baseline.py`，2483 行。
- 新建 `thesis/experiments/llm_probe/configs/shared_b0_distilbert_seed42_v1.yaml`，49 行。
- 新建 `thesis/experiments/llm_probe/tests/test_shared_b0_distilbert_baseline.py`，428 行。
- 新建 `.Codex/docs/sdd/task-shared-b0-distilbert-baseline/task-1-report.md`。

## 未修改内容

- 未修改 `thesis/experiments/llm_probe/pyproject.toml`。该文件已有其他未提交改动，本任务保留 `python -m flow_probe.shared_b0_distilbert_baseline` 入口，避免混入现有差异。
- 未修改 `scripts/`、冻结数据、共享 B0 视图、Qwen、HGB、XGBoost、`output/` 文档或其他生产模块。
- 未提交或推送 Git。

## 实现内容

- 配置解析固定种子 `42`、阶段 `theory_selection`、协议状态 `review_pending`、阈值 `0.5` 和标签映射 `0=benign`、`1=malicious`。
- 模型规范标识固定为 `distilbert/distilbert-base-multilingual-cased`，默认本地路径固定为 `/root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased`。
- 配置、冻结输入、模型镜像指纹和恢复绑定全部通过后，才延迟导入 `torch`、`transformers` 与 `swanlab`。
- 冻结输入只读取 `candidate/bert_train.parquet`、`validation/genis_bert.parquet` 和 `validation/tqhc2_bert.parquet`。
- 三份输入严格限制为 `sample_id`、`stable_order`、`text`、`label` 四列，并核验发布状态、文件大小、SHA-256、连续顺序、唯一主键、非空文本、合法标签、样本计数和三划分互斥。
- 输入绑定保存标签映射、三文件路径、大小、SHA-256、样本数、顺序哈希和冻结发布清单绑定。
- 训练使用 `AutoTokenizer`、`AutoModelForSequenceClassification`、确定性种子、梯度累积、自动精度、AdamW、线性预热衰减和梯度裁剪。
- 检查点保存模型、分词器、优化器、调度器、梯度缩放器、随机状态和选模状态；恢复时选择步数最大的绑定一致且哈希完整的检查点。
- GeNIS 只用于逐轮开发评价和宏平均 F1 选模；TQH-C2 仅在模型冻结后进入一次性外部评价阶段，不参与学习率、轮数、批量或阈值选择。
- GeNIS 与 TQH-C2 分别保存逐样本恶意概率、预测、真实标签、`sample_id` 和 `stable_order`。
- 指标包含准确率、宏平均 F1、良性 F1、恶意 F1、恶意召回率、良性误报率、平衡准确率、期望校准误差、布里尔分数、吞吐和延迟。
- 运行状态原子保存 `prepared`、`running`、`interrupted`、`failed`、`finished`，最终制品清单也原子写入。
- SwanLab 每个优化步记录损失和学习率，每轮记录完整 GeNIS 开发指标，最终记录两份评价指标，并在成功或异常路径显式调用 `finish`。
- CPU 正式训练会结构化退出；独立 `--cpu-forward-smoke` 模式可完成非最终 GeNIS 样本的最小前向。

## 测试覆盖

- 真实配置在模型运行时导入前可解析。
- 冻结三文件发布绑定、标签映射和顺序合同。
- 文件哈希不一致拒绝。
- 训练、GeNIS 与 TQH-C2 样本重叠拒绝。
- 非连续 `stable_order` 和非法标签拒绝。
- 检测、校准和布里尔指标的确定数值。
- 纯 CPU 小模型桩前向及批次顺序。
- 最新合法检查点选择和 `interrupted` 到 `prepared` 恢复。
- SwanLab 标量扁平结构、标签长度和显式结束。

## 验证记录

- 失败：`python3 -m py_compile src/flow_probe/shared_b0_distilbert_baseline.py tests/test_shared_b0_distilbert_baseline.py`。系统 Python 在解析前尝试写入沙箱禁止的用户字节码缓存目录，报 `PermissionError`；失败与源码语法无关。
- 通过：`python3 -c 'import sys; from pathlib import Path; [compile(Path(path).read_text(encoding="utf-8"), path, "exec") for path in sys.argv[1:]]' src/flow_probe/shared_b0_distilbert_baseline.py tests/test_shared_b0_distilbert_baseline.py`。两份文件均完成不落盘语法编译，退出码为 `0`。
- 首次未执行到格式器：沙箱内 `uv run --frozen black ...` 因无权读取现有 `~/.cache/uv` 而退出。
- 通过：批准读取既有 uv 缓存后，对两份新增 Python 文件集中执行一次 `uv run --frozen black ...`，两份文件均已格式化。
- 已完成唯一一次 Ruff：`uv run --frozen ruff check src/flow_probe/shared_b0_distilbert_baseline.py tests/test_shared_b0_distilbert_baseline.py`。只报告导入排序 `I001` 和可改用 `contextlib.suppress` 的 `SIM105` 两项风格建议，没有语法或结构问题；按仓库规则接受结果，未修改且未重复运行 Ruff。

## 未运行项

- 未在本机运行任何 `pytest`。
- 未读取真实冻结数据。
- 未下载或加载 DistilBERT 权重。
- 未执行 CPU 前向冒烟。
- 未执行服务器同步、依赖安装、GPU 训练、正式评价或 SwanLab 在线运行。

## 预期运行制品

- 唯一运行根目录：`runs/baselines/shared-b0-distilbert-seed42-theory-selection-review-pending-v1/`。
- 状态与绑定：`run_state.json`、`run_binding.json`、`input_binding.json`、`model_binding.json`、`config_snapshot.json`。
- 训练与选模：`checkpoint-<step>/`、`model-selection/`、`development_history.jsonl`、`swanlab_metrics.jsonl`。
- 评价与成本：`predictions/`、`metrics/`、`summary.json`、`cost.json`、`environment.json`。
- 最终登记：`artifact_manifest.json`。

## 风险与阻塞项

- 服务器当前没有 DistilBERT 权重，默认本地路径尚不存在。必须从官方 Hugging Face 精确模型取得权重并核对本地镜像指纹，禁止替换为英文 `distilbert-base-cased`。
- 生产模块为 2483 行，代码体量明显高于最小入口的理想规模，增加独立审查和服务器行为验证成本。本任务按指令停止扩展，不在当前实现代理内重构。
- 本机没有真实数据和模型，因此 Hugging Face 保存恢复、自动精度、GPU 内存口径和 SwanLab 在线生命周期尚未经过行为验证。
- Ruff 保留两项不影响执行的风格建议；服务器审查若认定其影响项目一致性，可在后续最小修复任务中处理。
- TQH-C2 一旦进入 `running` 状态，入口会拒绝自动重复外部评价；异常恢复需要独立审查具体制品后决定，避免隐式重复使用外部验证集。
