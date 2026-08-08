# E2 DistilBERT 训练适配器实现报告

## 结论

已补齐 E2 普通 DistilBERT 的完整源域训练适配器。适配器只接收源域训练集与源域校准集，模型文本严格限制为冻结七字段；C 域样本仅在选模结束后通过统一概率接口做逐样本预测，不能进入训练、类别权重、早停或阈值选择。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/e2_distilbert.py`
- `thesis/experiments/llm_probe/src/flow_probe/e2_hard_domain_baselines.py`
- `thesis/experiments/llm_probe/tests/test_e2_distilbert.py`
- `thesis/experiments/llm_probe/tests/test_e2_hard_domain_baselines.py`

未修改 E2 数据模块、指标模块、共享 PINN、包装器、配置、恢复文档和既有共享 B0 实现；`pyproject.toml` 已有 `torch` 与 `transformers` 可选依赖和 E2 命令入口，因此无需修改。

## 实现内容

- `E2DistilBertTrainingSettings` 沿用共享 B0 的普通多语言 DistilBERT、最大长度 128、批大小 16/64、梯度累积 2、学习率 `2e-5`、权重衰减 `0.01` 和三轮训练默认值。
- 输入门禁要求文本按固定顺序且仅由 `duration`、`orig_bytes`、`resp_bytes`、`orig_pkts`、`resp_pkts`、`orig_ip_bytes`、`resp_ip_bytes` 构成。
- 训练类别权重只从源域训练标签计算；早停和最佳模型选择只读取源域校准标签；最终阈值仍由原 E2 调度器在源域校准集选择。
- 复用共享 B0 的运行时加载、可复现种子、设备与精度选择、自动混合精度、梯度缩放、线性预热调度、二分类指标和概率前向函数。
- `device=auto` 在无 CUDA 时降级为 CPU；`precision=auto` 按 CUDA 能力选择 `bfloat16` 或 `float16`，CPU 使用 `float32`。显式 CPU 与非 `float32` 组合会降级到 `float32`。
- `SharedB0DistilBertPredictor` 增加固定批量前向，避免把完整 C 域一次送入显存，同时保持输入顺序。
- E2 命令入口在显式选择 `--model distilbert` 时创建训练适配器，并把训练设备、精度、优化步数、最佳轮次和源域校准指标写入 `distilbert_training.json`。
- 新增微型内存模型测试，覆盖实际优化器更新、源域校准选模和批量概率输出，不下载模型、不读取真实数据。

## 验证状态

按任务约束，未在本机运行 `pytest`、格式化、完整检查或 GPU 训练。同步服务器后只运行以下一次最小目标验证：

```bash
cd /root/autodl-tmp/thesis/experiments/llm_probe && uv run --no-sync pytest -q tests/test_e2_distilbert.py tests/test_e2_hard_domain_baselines.py -k distilbert
```

该命令应覆盖训练适配器的微型完整路径、源域隔离、批量预测顺序和设置门禁；不下载正式模型，也不启动正式实验。

## 遗留风险

- 本报告记录的是实现完成状态，不等于服务器目标验证已通过。
- 正式 DistilBERT 使用三轮训练，而 `E2BaselineBudget.max_iterations` 继续控制传统迭代模型；两类算法以相同字段、划分、阈值来源和数据可见性保证比较公平，不把不同优化器的迭代次数机械设为相同。
- 当前适配器在内存中保留源域校准最佳模型，正式检查点、SwanLab 逐步记录与中断恢复应由 E2 任务 4 包装器统一负责。
