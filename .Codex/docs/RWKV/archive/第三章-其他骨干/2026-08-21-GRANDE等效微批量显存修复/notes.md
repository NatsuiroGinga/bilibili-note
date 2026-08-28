# GRANDE G-B 等效微批量显存修复证据笔记

## 修改前快照

- 工作树已有其他代理修改，禁止覆盖、回滚或暂存。
- GRANDE 工具 SHA-256：`fb97c307f76fbf878fdc6293c2efec824f2d903b574f189d4605adf5d7a8345b`。
- 原配置 SHA-256：`f7d0358e983c19f5109a42f9ce9fcb6b61874d76b18ff390120d7d6c684d2b92`。
- 原启动器 SHA-256：`6e1424c5d8e97878dd1619a7ec79296acefda3999f52e481e1aec7494d6120b8`。
- GRANDE 核心 SHA-256：`caf94daf71cec89ac7a53705f8628b41f223966d6c70abf741426fda7a3370e6`。
- 运行上限撤销说明 SHA-256：`7b40a852f70679529e0f5000a119dce0987db340703af6b35484b14c76c68040`。
- 三个既有 GRANDE 生产文件相对 `HEAD` 的二进制差异摘要：`71f836d8e1981cc51ff71ff35ee49c8f0c62d44fcd03c8d9294d8d566cf51071`。
- 新任务目录修改前不存在，当前 `HEAD` 构成其空状态快照。

## 根因证据

- G-A 深度 4、512 棵树的 FP32 训练已完成 20 周期，已有 `selection-G-A`、完整预算曲线和选择检查点。
- G-B 深度 5、1024 棵树在一个原始批次约 8192 个有效流上反向传播时显存溢出。
- 溢出时进程占用约 `30.05 GiB`，GPU 空闲约 `1.30 GiB`，额外申请约 `3.04 GiB`；已启用 `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`，因此不是仅靠分配器配置可解决的碎片问题。
- 固定核心形成与有效流数成线性比例的 `batch × 1024 × 32` 路径张量及多组路由中间量，完整展平批次使反向激活峰值超过 RTX 5090 容量。
- 目标年数组读取数为 0；显存修复不得借用任何目标指标。

## 微批资源合同

- 原始批次容量上界为 `64 × 128 = 8192` 个有效流。
- 正式 FP32 微批上限固定为 `8192 / 4 = 2048` 个有效流，是失败容量上界的四分之一且为 2 的幂。
- 该值只根据模型张量形状、原始批次容量与显存溢出收据确定，不使用验证 AP、实体 AP、最终标签或任何效果指标。
- 每个原始优化步仍覆盖同一批全部有效流。微批仅改变计算调度，不改变采样、损失分母、模型、有效批、周期或优化步数。

## 数学等价合同

设一个原始优化步包含 `N` 个有效流，逐流带类别权重的二元交叉熵为 `l_i`，完整批次损失为：

`L = (1 / N) × Σ_i l_i`。

将有效流不重不漏地划分为微批集合 `S_k` 后，每个微批反向传播：

`L_k = (1 / N) × Σ_{i∈S_k} l_i`。

梯度累积满足：

`Σ_k ∇L_k = ∇[(1 / N) × Σ_i l_i] = ∇L`。

因此必须使用每微批 `reduction="sum" / total_valid_flows`，禁止使用微批均值再平均；每个原始批次只允许一次清梯度、一次裁剪和一次优化器更新。

## 第三方 API 核验

- 核验日期：2026-08-21。
- 库：PyTorch；项目合同目标运行版本为 `2.13.0`，上游 GRANDE 声明范围为 `>=2.6,<2.10`，真实兼容性仍由既有 R0 收据限定。
- 来源：Context7 高信誉 `/pytorch/pytorch`，对应 PyTorch 官方源码和文档。
- BF16 接口：`torch.amp.autocast("cuda", dtype=torch.bfloat16, enabled=...)`；CUDA 默认 autocast 精度是 FP16，故 BF16 必须显式指定，运行前须检查 `torch.cuda.is_bf16_supported()`。
- 激活检查点接口：`torch.utils.checkpoint.checkpoint(function, *args, use_reentrant=False)`；默认保留随机数状态，非重入实现支持默认确定性形状、类型和设备核验。

## 技能与仓库冲突裁决

- `writing-plans` 和通用调试技能建议测试驱动、回归测试及频繁提交。
- 仓库规则禁止为实验工程创建或运行人工夹具、单元测试和集成测试，也禁止 `black`，并要求不让格式化延迟真实实验。
- 本任务采用仓库高优先级规则：不创建测试夹具、不运行 `black`，只执行父任务明确授权的一次语法、导入、帮助、配置、启动器和数学归一化静态核验。
- 共享暂存区若非空则不提交，避免夹带其他代理改动。

## 实施结果

- 新配置：`thesis/experiments/llm_probe/configs/ch3-grande-c00-protocol-a-source-q0-seed42-v1-rerun1.json`。
- 新入口：`thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_grande_c00_protocol_a_source_q0_seed42_v1_rerun1.sh`。
- 共享工具新增运行身份白名单、G-A 迁移、G-B FP32 流微批、优化步边界恢复、BF16 候选、激活检查点分支和显存收据。
- vendor 核心只新增 FP32 softmax、对数诊断和权重归一化保护，树路径与输出公式未改变。
- 启动器仍以 5 秒间隔记录外部 `nvidia-smi` 显存，并在最终资源收据写入峰值。

## 静态验证

- `py_compile`：工具与 vendor 核心通过。
- 导入检查：通过，`RERUN_RUN_ID` 与 `training_logits` 可见。
- `--help`：通过，命令入口可解析。
- `--validate-config`：新 `rerun1` 配置通过。
- `bash -n`：共享启动器与新包装入口通过。
- JSON 与 vendor 摘要：通过；清单中的核心 SHA-256 与文件一致。
- 损失归一化：使用二元交叉熵解析梯度核验，完整均值梯度与分块 `sum / total_valid_flows` 累积梯度最大绝对差为 0。
- `git diff --check`：通过。

## 验证边界

- 本地 `uv --no-sync` 环境未安装 PyTorch，张量级梯度对照报 `ModuleNotFoundError: No module named 'torch'`；未联网安装依赖。
- Context7 已完成接口签名核验，但本轮按任务边界未访问服务器、未运行真实 GPU 前向、未启动训练。
- Prettier 被仓库 `P0-NO-PRETTIER` 钩子明确阻止；JSON 已通过标准库解析，不绕过钩子。
- 因共享暂存区非空，本任务不暂存、不提交任何文件。
