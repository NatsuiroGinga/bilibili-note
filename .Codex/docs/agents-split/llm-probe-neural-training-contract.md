# llm_probe 神经训练按需合同

本文件承接只在新增或修改神经模型、训练循环、混合精度、显存优化、`DataLoader`、推理模式或检查点时触发的强制细节。当前服务器、运行身份和 profile 以路线总控、冻结配置和真实环境为准，不在本合同写死。

## 接口与精度

- 实施前调用并读取 `$pytorch-patterns`，核验目标环境实际安装版本及所用接口，在计划或报告记录技能条目、版本、官方来源和签名。
- 新神经训练默认从 `configs/neural-precision-profiles-v1.json` 读取 `cuda-bf16-amp-fp32-sensitive-v1`，经 `tools/neural_precision_runtime.py` 接入：BF16 autocast；参数、优化器状态以及 softmax、对数、归一化和损失保持 FP32；BF16 不用 `GradScaler`。
- FP32、FP16 和 activation checkpointing 只作有收据的显式例外；FP16 走已核验缩放路径。每个合同预注册精度与启用条件，活动运行不得中途切换精度。
- 同族结构、机制、消融和选型的科学比较必须使用同一 profile；跨 profile 只作完整系统或工程 Pareto。异精度结果只作工程资格观察，除非补做同精度对照。

## 容量、有效批与 OOM

- 资源估算按真实展开张量上界，写明批量、长度以及树、头、叶、层等并行维度乘积、类型字节与反向保留量，不得只按参数量。
- OOM 首选数学等效微批量和梯度累积：有效批起点一次 `zero_grad(set_to_none=True)`，微批损失按 `sum` 累加后除以全部有效样本数，有效批结束一次裁剪和 `optimizer.step()`，尾批按真实样本归一。
- 数学等效微批仍不安全时才考虑 activation checkpointing；禁止缩小冻结模型、序列、有效批量、训练步数或评价来伪装修复。

## 检查点、模式与收据

- 检查点只写在完整 `optimizer.step()` 边界，保存模型、优化器、缩放器（如有）、随机状态、采样器、精度、微批量和累积步数；半步中断从有效批起点重放，不恢复部分累计梯度后跳过样本。
- 训练、验证和推理明确 `model.train()`、`model.eval()` 与梯度模式，设备无关放置并记录 CUDA、MPS、CPU 回退限制；推理只在已核验接口下用 `torch.no_grad()` 或 `torch.inference_mode()`。
- 每次运行收据至少含设备、精度、有效批量、微批量、累积步数、张量上界、峰值主存、磁盘、检查点边界、恢复次数和 OOM 或数值异常；最坏候选首次真实 `optimizer.step()` 记录 `allocated`、`reserved`、`max_allocated`、`max_reserved` 与外部进程显存。
- 不设置人为墙钟或 GPU 小时上限；资源不安全时停止并保留收据，不改变已冻结的科学合同。
