# 共享 B0 树模型基线实现报告

## 结论

共享 B0 的 HGB/XGBoost 严格装载、统一执行和一次性正式启动入口已经落盘。本机只完成格式化与静态门禁，服务器 `pytest`、同步、SwanLab 运行和正式实验尚未执行。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/shared_b0_tabular_baselines.py`
- `thesis/experiments/llm_probe/tests/test_shared_b0_tabular_baselines.py`
- `thesis/experiments/llm_probe/scripts/run_shared_b0_tabular_baselines.sh`
- `.Codex/docs/sdd/task-shared-b0-tabular-baselines/task_plan.md`
- `.Codex/docs/sdd/task-shared-b0-tabular-baselines/notes.md`
- `.Codex/docs/sdd/task-shared-b0-tabular-baselines/implementation-report.md`

未修改 `pyproject.toml`、`shared_b0_view.py`、`tabular_baselines.py`、生成式评测文件、`output/` 文档和其他任务文件。

## 实现要点

- 严格接受 `flow_probe_shared_b0_view_v1` 且状态为 `theory_selection/review_pending` 的原子发布目录。
- 验证 `freeze_manifest.json`、`checksums.json`、`input_binding.json` 和 `statistics.json` 的绑定与状态。
- 逐个复核以下六个输入的登记大小和 SHA-256：
  - `candidate/common_features.parquet`
  - `candidate/bert_train.parquet`
  - `validation/genis_common_features.parquet`
  - `validation/genis_bert.parquet`
  - `validation/tqhc2_common_features.parquet`
  - `validation/tqhc2_bert.parquet`
- 公共特征必须严格为共享视图的 8 个字段和 8 个缺失掩码；标签文件只投影主键、顺序和 `label`。
- 训练与验证视图按行核对 `sample_id` 和 `stable_order`，验证唯一性、连续性及跨划分无重叠。
- 通过现有 `PreparedTabularData` 和统一执行器复用 HGB、XGBoost、评价、预测与成本逻辑；正式制品复用现有 SwanLab 跟踪生命周期。
- 正式脚本不依赖 CUDA 或 `nvidia-smi`，保存代码/输入绑定、能力清单、完整管道状态和非空启动日志。

## 直接测试覆盖

- 正常装载只产生 16 维公共数值特征，标签只作为监督目标。
- 登记制品被篡改时在读取前拒绝。
- 哈希刷新后仍拒绝标签视图行序错配、重复主键和公共特征中的额外 `label` 列。
- HGB 冒烟直接经过现有统一执行、评价、预测和成本路径。
- 正式跟踪入口在数据加载前拒绝已有输出目录。

## 本地验证

- `Black`：2 个 Python 文件格式化成功。
- `Ruff`：首次检查仅报告 `I001` 导入排序风格项，无语法或结构问题；按局部规则接受且未重复运行。
- `.venv/bin/python -m py_compile src/flow_probe/shared_b0_tabular_baselines.py tests/test_shared_b0_tabular_baselines.py`：退出码 0。
- `bash -n scripts/run_shared_b0_tabular_baselines.sh`：退出码 0。
- `git diff --check`：退出码 0。
- 本机未运行 `pytest`，符合实验目录规则。

## 服务器待执行

1. 同步三个实验文件并核对 SHA-256。
2. 运行 `uv run pytest tests/test_shared_b0_tabular_baselines.py -q`。
3. 最小测试通过后运行 `bash scripts/run_shared_b0_tabular_baselines.sh`。
4. 核对唯一输出目录、退出状态、摘要、成本、预测、SwanLab 云端标量和图表。

## 运行制品

- 计划服务端输出：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/baselines/shared-b0-tabular-seed42-theory-selection-review-pending-v1`
- 当前未生成本地或服务端正式运行制品。

## 遗留风险

- 尚未在真实 `dataset-v1-shared-b0` 和服务器依赖环境上运行测试。
- 独立代码审查尚未完成，正式运行与结果必须保持 `review_pending`。
- 新入口直接调用现有树模型模块的内部统一执行函数；后续若该内部接口变更，直接测试必须先行失败并阻止实验。
