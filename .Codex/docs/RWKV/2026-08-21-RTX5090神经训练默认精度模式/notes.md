# RTX 5090 神经训练默认精度模式证据笔记

## 修改前快照

- 独占任务目录、共享工具与两个配置文件在任务开始时均不存在，目标路径 `git status --short` 为空，当前 `HEAD` 可作修改前快照。
- 共享暂存区在任务开始时为空。
- 工作树存在大量其他代理的未提交改动，本任务不覆盖、不回滚、不暂存这些文件。
- 跨进程看板在首次检查时工作树干净；是否修改仍须在实际编辑前再次检查。

## 规则与技能

- 已读取根 `AGENTS.md`、`thesis/experiments/llm_probe/AGENTS.md`、`.Codex/docs/AGENTS.md` 和 `.Codex/docs/RWKV/AGENTS.md`。
- 已读取 `planning-with-files`、`writing-plans`、`daily-coding` 与 `/Users/bilibili/.codex/skills/pytorch-patterns/SKILL.md`。
- 采用的 `pytorch-patterns` 条目：设备无关放置、`optimizer.zero_grad(set_to_none=True)`、混合精度、缩放后先反缩放再裁剪、完整检查点、随机状态与 activation checkpointing 的显式权衡。
- 与技能默认示例的冲突：技能示例把是否存在缩放器作为是否启用 autocast 的条件，并展示默认 `torch.compile`、`drop_last=True`。本合同明确 BF16 autocast 不使用缩放器、尾批不得丢弃、`torch.compile` 默认关闭，因此以仓库规则和冻结任务规格为准。

## PyTorch 官方接口核验

- 目标运行时：仓库锁与环境收据指向 PyTorch `2.13.0+cu130`；本任务不访问服务器，未重新探测目标环境。
- Context7 库查询返回高信誉官方仓库 `/pytorch/pytorch`，可选固定网页最高为 PyTorch 2.12，没有 2.13 精确版本页面。
- `/pytorch/pytorch` 官方源码与文档核验：`torch.amp.autocast(device_type, ...)` 为统一 AMP 上下文；`torch.amp.GradScaler(device="cuda", init_scale=2**16, growth_factor=2.0, backoff_factor=0.5, growth_interval=2000, enabled=True)`；旧 `torch.cuda.amp` 与 `torch.cpu.amp` 入口已弃用。
- PyTorch 2.12 官方文档核验：CUDA BF16 能力接口为 `torch.cuda.is_bf16_supported(including_emulation=True)`；梯度缩放路径必须先 `scaler.unscale_(optimizer)` 再裁剪，随后 `scaler.step(optimizer)` 与 `scaler.update()`。
- 官方 CUDA 说明核验：内部资源接口包括 `torch.cuda.memory_allocated`、`memory_reserved`、`max_memory_allocated`、`max_memory_reserved` 与 `reset_peak_memory_stats`。
- 2.13 精确文档缺失的处理：本工具只使用上述在官方当前源码与 2.12 文档中同时成立的统一入口；正式接入前仍须在目标 `2.13.0+cu130` 环境运行配置门和第一完整优化器步资源收据，不能把本地语法检查当作 2.13 运行证明。

## 资源证据

- 硬件收据：RTX 5090，显存总量 `32607 MiB`，计算能力 `12.0`。
- TabM4 协议 A 本地回收收据：外部 `nvidia-smi` 峰值 `14644 MiB`；既有进程内报告约 `13646 MiB`。TabM32 计划估算双年常驻数组约 `11.66 GiB`，说明参数量不是峰值显存的充分代理。
- GRANDE G-B 失败收据：完整原始批次最多 `8192` 个有效流，核心展开 `batch × 1024 trees × 32 leaves` 路径张量；反向 OOM 时进程约 `30.05 GiB`，仍需约 `3.04 GiB`，分配器可扩展段已开启，不能归因于简单碎片。
- GRANDE 新运行状态只作工程瞬时证据：`2048` 流 FP32 等效微批量在资源标定阶段约占 `31132/32110 MiB`，仍未形成工程通过或科学结果。
- RWKV-7 放大容量把 `r/w/k/v/a/b` 与递归矩阵状态声明为 FP32；该事实要求通用合同允许模型显式登记递归敏感区，而不是强制所有算子 BF16。
- 全容量 MLP 入口已记录进程内 `max_memory_allocated` 和有效流吞吐，但既有收据字段不完整覆盖 `reserved/max_reserved/external`；新合同补齐这些字段，不能追溯性声称旧实验已满足。

## 决策

1. 默认配置 `cuda-bf16-amp-fp32-sensitive-v1` 是基于 RTX 5090 BF16 能力、现有 FP32 显存事故与训练速度压力选择的工程默认，不是本项目全模型精度效果 A/B 已证明的最优配置。
2. 模型参数与优化器状态保持 FP32；BF16 只覆盖允许 autocast 的前向区域。敏感算子和模型声明的递归/路由状态由 `fp32_island` 显式转 FP32。
3. CPU/MPS 不跟随 CUDA BF16，默认 FP32。FP16 是无 BF16 CUDA 设备的显式回退并启用缩放器；FP32 必须引用数值异常收据。
4. 有效批与归一化单位分离：实验合同冻结有效批对象数，模型显式声明 `flow/sequence/entity`；运行时按每个原始步实际有效单位总数归一化，尾批不补不丢。
5. activation checkpointing、`torch.compile` 和 TF32 均默认关闭。前者只在 BF16 加等效微批仍不够时显式启用并记收据，后二者不得由共享工具静默改变。
6. 后续效果验证使用 LSPR23 源年代表模型，至少覆盖普通前馈骨干和带递归或路由敏感区的骨干；验证前不得称默认配置已实验证明最佳。
