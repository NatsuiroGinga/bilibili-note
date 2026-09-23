# DRIFT MPS 迁移分段诊断实施计划

> **实施范围**：本计划只定位 24M DRIFT 双分支 Transformer 在本机 MPS 的启动延迟；它不改变论文训练子集、模型结构、嵌套张量设置、训练公式或正式合同。

**目标：** 以真实 DRIFT 开发数据和官方 24M 架构，将模型构造、权重读取、状态写入、迁移 MPS、首个前向和首个反向的墙钟与资源状态分别持久化，定位初始化卡点。

**依据：** [源期训练抽样研究问题卡](../../../thesis/methods/第三章-DRIFT源期训练抽样合同研究问题卡.md)、[MPS 初始化诊断简报](MPS初始化与时长诊断简报.md)。进程采样已显示主线程停在 `model.eval().to(mps)` 的 `MPSStream::copy_and_sync`／Metal command-buffer 等待；`torch.mps.synchronize()` 的 PyTorch 2.12 官方文档已核验。

## 全局约束

- 工程代码只由 `gpt-5.6-luna` 实现；本任务选择 `high`，因为需复用官方双分支模型、真实编码和阶段状态，错误会误导后续硬件选择。
- 只新建一个诊断工具与报告／技能收据；不修改现有训练脚本、模型源码、配置或数据合同。
- 输入使用既有 T17 良性／DGA 训练 Parquet 的真实开发批，批量固定为既有筛选主批 `128`；仅用于资源诊断，不产生模型效果结论。
- 仅写小型阶段 JSON／JSONL、控制台和资源收据；不得写模型、成员清单、域名、攻击数据、副本、缓存或索引。
- `torch.mps.synchronize()` 只在 MPS 可用时、每个被测设备阶段结束时调用；所有阶段先原子写 `running` 状态，再执行耗时操作。
- 禁止人工夹具、单元／集成测试、自动格式化、训练多轮、服务器连接和 Git 写操作。真实开发批诊断由主代理在代码验收后启动。

## 任务 1：独立 MPS 分段诊断工具

**文件：**

- 新建：`thesis/experiments/llm_probe/tools/ch3_drift_mps_startup_diagnostic.py`
- 新建：`.Codex/docs/2026-09-23-DRIFT源期训练抽样合同/mps-startup-diagnostic-report.md`
- 新建：`.Codex/docs/2026-09-23-DRIFT源期训练抽样合同/mps-startup-diagnostic-skill-receipt.json`

**职责：**

1. 仅接受 `--run-dir`、`--batch-size`；拒绝绝对路径、非正批量和非 MPS 环境。路径通过既有 `resolve_run_dir` 约束在 `llm_probe/runs`。
2. 固定复用官方快照、`finetuning.pt`、tokenizer、`FineTuningModel`、编码和分类头语义；先构造两个 `PretrainedModel` 和 `FineTuningModel`，再 `torch.load(..., map_location="cpu", weights_only=True)`、`load_state_dict(strict=True)`、`model.eval().to(mps)`。
3. 按顺序写入并计时：`construct_model`、`load_state_dict_file`、`apply_state_dict`、`move_model_to_mps`、`load_real_batch`、`first_forward`、`first_backward`。每个 MPS 阶段完成后调用 `torch.mps.synchronize()`，因此报告的是实际 Metal 完成时间。
4. 实际批从当前 T17 两类训练文件各读取相同数量，使总批为128；保留原域名只在进程内，使用现有 token／character 编码。前向使用模型真实双分支与分类头；反向对真实交叉熵执行一次 `backward()`，不创建优化器步骤、不写模型、不更新权重。
5. 每阶段记录单调耗时、RSS、磁盘可用字节、设备、代码／模型／输入哈希、状态与异常类别。若在阶段内被终止，最后落盘的 `running` 阶段就是卡点；不得将缺失的后续阶段标作通过。

**验收：**

- 语法和 `--help` 可用；模块导入不执行模型构造或读 Parquet。
- 真实诊断在独立运行目录保存阶段状态，至少能记录终止前的精确阶段；不包含域名／成员／攻击明文，也不写模型或数据副本。
- 报告区分“启动资源证据”与“训练或方法效果证据”；记录 PyTorch 2.12、`torch.mps.synchronize()` 官方来源和实际函数签名。

## 任务 2：主代理真实运行与裁决

**主代理动作：** 仅在任务1验收后，以本机唯一解释器运行独立目录的真实开发批诊断；启动前核对无其他训练进程、磁盘余量和 MPS 可用性。

**读取证据：** `phase-status.json`、`timing.json`、`resource.jsonl`、控制台及进程采样（仅当阶段持续未结束）。

**裁决规则：**

- `move_model_to_mps` 是最长阶段：进入下一轮“迁移路径”单变量诊断；不先改 nested-tensor 或批量。
- `first_forward`／`first_backward` 才是最长阶段：单独诊断嵌套张量回退与 CPU↔MPS 特征回传。
- 诊断无法完成、资源异常或输入身份不符：保留收据，停止受影响的本机训练路线；不能据此否决 DRIFT 方法或改论文子集。

## 实施前审阅

- 本计划没有抽样规模、训练轮数、优化器、阈值或模型效果门槛；这些仍由论文专用子集覆盖与时长诊断决定。
- 任务1不与现有训练脚本共享写状态，任务2只消费其诊断输出；不存在文件所有权冲突。
- 唯一外部接口为 PyTorch 2.12 的 `torch.mps.synchronize()`，已在官方文档核验为无参数阻塞同步。
