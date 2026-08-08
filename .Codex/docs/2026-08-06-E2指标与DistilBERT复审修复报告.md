# E2 指标与 DistilBERT 复审修复报告

## 结论

独立复审中的指标与普通 DistilBERT 两个阻断项已完成代码修复。指标改用标准平均精度定义并增加同分样本重排不变性回归断言；DistilBERT 只接受与预注册 SHA-256 摘要一致的本地基础预训练镜像，加载后显式重置二分类头，并把来源权重清单与分类头初始化摘要写入训练收据。

本报告只说明实现已落盘，不宣称服务器目标测试或正式训练已经通过。

## 根因

### 指标

旧实现先稳定排序，再逐个正样本按所在秩累计精度。同分概率没有按唯一阈值整体处理，因此同一批标签与概率只要重排同分样本就可能产生不同结果。之前测试中的 `0.75` 期望固化了该错误口径。

### DistilBERT

旧实现只检查模型目录存在，随后直接调用序列分类模型加载器。当来源目录包含形状相同的旧二分类头时，该分类头会被继承；训练摘要也没有绑定基础权重文件及其 SHA-256，无法证明对比项从冻结基础模型开始。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/e2_hard_domain_metrics.py`
- `thesis/experiments/llm_probe/tests/test_e2_hard_domain_metrics.py`
- `thesis/experiments/llm_probe/src/flow_probe/e2_distilbert.py`
- `thesis/experiments/llm_probe/tests/test_e2_distilbert.py`
- `thesis/experiments/llm_probe/src/flow_probe/e2_hard_domain_baselines.py`
- `thesis/experiments/llm_probe/tests/test_e2_hard_domain_baselines.py`
- `.Codex/docs/2026-08-06-E2指标与DistilBERT复审修复报告.md`

未修改数据、共享 PINN、包装器、配置和恢复文档。

## 实现内容

### 统一指标

- 使用 `sklearn.metrics.average_precision_score` 替换逐秩实现。
- 保持现有 `pr_auc` 输出键，数值口径改为标准平均精度。
- 将既有同分样本用例的期望从 `0.75` 修正为 `0.5`。
- 新增同分样本重排不变性断言，要求相同标签—分数多重集合在改变输入顺序后得到相同结果。

### 基础模型来源绑定

- 新增必填的 `expected_model_binding_sha256`，只接受 64 位小写 SHA-256。
- 复用共享 B0 的模型来源核验，要求本地镜像、固定 DistilBERT 指纹、完整权重文件清单和逐文件 SHA-256。
- 实际模型绑定摘要必须与预注册值精确一致。
- `config.json` 的 `architectures` 只允许 `DistilBertForMaskedLM` 或 `DistilBertModel`；声明为序列分类模型或来源不明的检查点会被拒绝。
- 命令入口新增 `--distilbert-model-binding-sha256`，正式运行必须显式提供预注册摘要。

### 分类头隔离与运行收据

- 模型加载后、训练前，按当前运行种子显式重置 `pre_classifier` 和 `classifier`。
- 记录重置前后分类头参数摘要；摘要未变化时拒绝训练。
- `distilbert_training.json` 对应的训练摘要升级为 `flow_probe_e2_distilbert_training_v2`，新增：
  - 基础模型绑定摘要；
  - 权重文件名、大小和 SHA-256；
  - 分类头重置模式、种子、组件和重置前后参数摘要。

## 验证状态

按任务约束，未在本机运行 `pytest`、格式化、静态检查或训练，也未同步服务器。已通过逐段源码核对确认修改落在授权文件范围内。

服务器同步后只需运行一次最小相关检查：

```bash
uv run --no-sync pytest -q tests/test_e2_hard_domain_metrics.py tests/test_e2_distilbert.py tests/test_e2_hard_domain_baselines.py -k 'pr_auc or tied_scores or distilbert or base_model_binding'
```

## 遗留边界

- 正式运行前必须先对服务器上的基础模型目录计算共享 B0 模型绑定摘要，并把该值冻结到运行配置或命令参数；不得在训练失败后替换模型目录或摘要。
- 已经生成的旧 `PR-AUC` 结果必须从逐样本预测重新计算，不能继续作为论文证据。
- 本修复不处理独立复审中属于共享 PINN 的置换、字段、样本绑定、共同预算和共享梯度问题。
