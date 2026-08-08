# R2 DistilBERT 物理旁路三种子分析器实施报告

## 结论

已新增独立的三种子离线分析入口：

`thesis/experiments/llm_probe/src/flow_probe/r2_distilbert_multiseed_analysis.py`

该入口固定消费种子 `42/43/44` 的 `T-A`、`T-P`、`T-S`、`T-R` 十二组完成制品，输出逐种子指标、三种子均值与样本标准差、`P-A`、`P-S`、`P-R` 配对差值与自助法置信区间，并自动裁决 `T-P` 是否在三个种子上逐一同时超过三类对照。

本轮没有运行 GPU、模型训练、模型导入、SwanLab、真实结果分析或最终测试。当前只完成分析代码，不能据此报告探针结果。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/r2_distilbert_multiseed_analysis.py`
- `.Codex/docs/sdd/task-r2-physics-sidecar-signal/distilbert_multiseed_analysis_impl_report.md`

没有修改：

- `src/flow_probe/r2_distilbert_sidecar_probe.py`
- `configs/r2_distilbert_sidecar_probe_seed42.yaml`
- `configs/r2_distilbert_sidecar_probe_seed43.yaml`
- `configs/r2_distilbert_sidecar_probe_seed44.yaml`
- 既有运行制品与两份恢复文档

## 输入门禁

分析器在创建输出目录前完成以下只读断言：

1. 运行根精确包含种子 `42/43/44`，不接受缺失、替换或额外 `seed-*`。
2. 每个种子精确包含 `T-A/T-P/T-S/T-R` 四组。
3. 每组必须为 `finished / theory_selection / review_pending`，且 `final_test_visible=false`。
4. 每组必须存在并核验指标、预测、输入绑定、运行绑定、组汇总、种子汇总、制品清单、收尾收据和最佳模型收据。
5. `artifact_manifest.json` 与最终目录文件集合、大小和分析所需文件 SHA-256 必须一致。
6. `run_state.json` 按修复后的收尾合同单独核验，必须为 `finished`、`latest_checkpoint=null`、`failure=null`；它不要求登记到制品清单。
7. 完成组不得残留 `checkpoint-*`，`model-selection/` 必须只保留一个最佳模型。
8. 冻结输入摘要必须精确等于当前先导输入摘要、检测视图与 18 维旁路的三个预注册 SHA-256。
9. 十二组训练与验证的样本顺序、文本摘要、标签摘要和预测配对身份必须一致。
10. 十二组模型绑定、模型结构、参数合同、优化器和 `192` 步训练预算必须一致。
11. 十二组探针实现摘要和五项语义依赖摘要必须一致，并与分析时工作树中的实际文件 SHA-256 一致。
12. 预测只允许固定的七个字段，概率、阈值预测、标签名称和样本唯一性必须合法；四项核心指标从预测重新计算并与指标文件及组汇总逐项比较。
13. 疑似最终测试预测或指标路径会被拒绝；分析器不选择最好种子。

## 统计与裁决

每组报告：

- 宏平均 F1；
- 良性误报率；
- Brier 分数；
- 期望校准误差。

每个种子直接计算：

- `P-A`；
- `P-S`；
- `P-R`。

配对自助法固定在相同样本上按二分类真实标签分层抽样，默认重复 `2,000` 次。差值方向统一为 `T-P - 对照`。宏平均 F1 的正差值表示改善；良性误报率、Brier 分数和期望校准误差的负差值表示改善。

主裁决严格复现阶段二合同：只有 `T-P` 的宏平均 F1 在种子 `42/43/44` 上逐一同时严格超过 `T-A/T-S/T-R`，才输出 `GO_TO_QWEN`；否则输出 `NO_GO` 并逐项列出失败种子与比较对象。配对置信区间是否全部支持正差值另行报告为证据强度，不通过时不会被隐藏。

## 物理指标边界

当前公开 TQH-C2 开发验证没有隐藏队列真值，`T-A` 也没有对应状态头，因此分析器明确输出：

`not_evaluable_on_current_public_tqhc2_development_validation`

正式 R2 的未观测状态误差和物理残差相对同分区基线逐种子改善至少 `10%` 的门槛仍保留，但不能由当前探针伪造。既有 ns-3 状态估计器与旁路摘要只作为就绪背景绑定，不计入 `T-P` 相对 `T-A` 的物理增益。

## 输出合同

指定的全新输出目录包含：

```text
analysis_config.json
input_manifest.json
analysis_summary.json
metrics.csv
summary.md
artifact_manifest.json
```

其中 JSON 保存完整机器可读结果与自动裁决，CSV 保存逐种子与聚合长表，Markdown 保存人工可读摘要。当前任务不登记 SwanLab。

正式十二组结束后的调用形式：

```text
python3 -m flow_probe.r2_distilbert_multiseed_analysis \
  --run-root runs/r2-transformer-sidecar-probe/distilbert-v0 \
  --output runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1 \
  --bootstrap-repetitions 2000 \
  --bootstrap-seed 20260803
```

## 验证记录

本任务仅执行一次允许的编译检查：

```text
python3 -m py_compile thesis/experiments/llm_probe/src/flow_probe/r2_distilbert_multiseed_analysis.py
退出码：0
```

按任务约束未执行：

- Black、Ruff、Prettier 或其他格式化；
- Pyright 或其他静态类型检查；
- pytest、测试驱动开发或独立冒烟；
- Git 差异命令；
- 真实模块或模型导入；
- GPU、服务器训练、SwanLab 或联网操作。

## 遗留边界

1. 当前没有十二组真实完成制品，因此尚未执行端到端结果分析。
2. 分析器要求运行绑定中的代码摘要与分析环境实际文件一致；训练后若继续修改探针或五项语义依赖，必须保留对应运行代码快照或明确发布新合同，不能混用版本。
3. `GO_TO_QWEN` 只表示当前小型 Transformer 开发集探针通过预注册检测增量条件，不是论文最终结论，也不替代正式三源、多种子物理门槛与最终测试。
