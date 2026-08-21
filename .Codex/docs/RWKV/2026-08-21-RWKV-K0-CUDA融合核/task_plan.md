# RWKV K0 CUDA 融合核实施计划

> **实现约束**：本任务由已分派实现代理在独立工作树执行，按 `daily-coding` 清单先读后改。仓库禁止人工单元测试夹具，因此以结构化等价性与速度基准工具取代测试套件。

**目标：** 在不修改当前纯 PyTorch BF16 训练入口的前提下，为已封印 K0（`C=112`、`HEAD_SIZE=16`、`T=128`）新增 BlinkDL 官方 RWKV-7 基础 WKV 前反向 CUDA 融合后端、独立基准和远程启动入口。

**架构：** 保留官方提交 `952102498e9ed367ea0a59ee64106916d474d30f` 的 Apache-2.0 许可证和原始 `rwkv7_clampw` CUDA 源码，仅在独立派生 C++ 注册文件中改用项目专用算子命名空间。Python 后端以编译宏 `_N_=16`、`_CHUNK_LEN_=16` 加载未改动 CUDA 核，在入口机械断言 CUDA/BF16/连续性/形状/版本合同，通过 `torch.autograd.Function` 返回六输入梯度。基准工具独立导入当前 K0 模型仅作参照，不改写其类、全局后端或运行根。

**技术栈：** Python 3.11、PyTorch 目标 `2.13.0+cu130`、CUDA 13.0、RTX 5090 `sm_120`、C++/CUDA 扩展、BF16 输入输出、FP32 递归状态。

**依据：** `.Codex/docs/RWKV/2026-08-21-RWKV7官方CUDA融合核接入审计/notes.md`、`.Codex/docs/RWKV/RWKV第三章恢复卡.md`、`thesis/experiments/llm_probe/tools/ch3_rwkv7_field_aware_protocol_a_2x2_bf16.py`。

## 全局约束

- 只新增独占文件，不修改活动 BF16 工具、配置、启动器、运行根、恢复卡或服务器状态。
- 不访问服务器，不在本机宣称 CUDA 编译、前反向或性能通过。
- 不把 K0 改为 `C=128`，不新增 ChannelMix、PreLN、残差或官方完整块身份。
- 官方核接收 `w_raw`；当前纯 PyTorch 参照接收 `w_clamped=-softplus(-w_raw)-0.5`，基准必须避免二次 soft-clamp。
- 扩展编译目标仅限 `sm_120`；目标 PyTorch/CUDA/ABI 不符即停止，不静默回退。
- 只有合成公式对照、LSPR23 冻结首批、整轮吞吐与峰值显存全部达标，且选择指标一致，才允许另立融合核训练身份；否则保留纯 PyTorch。

## 文件所有权

- 新建：`thesis/experiments/llm_probe/vendor/rwkv7_k0_fused/`。
- 新建：`thesis/experiments/llm_probe/tools/rwkv7_k0_fused_backend.py`。
- 新建：`thesis/experiments/llm_probe/tools/ch3_rwkv7_k0_fused_benchmark.py`。
- 新建：`thesis/experiments/llm_probe/configs/ch3-rwkv7-k0-fused-benchmark-v1.json`。
- 新建：`thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_rwkv7_k0_fused_benchmark_v1.sh`。
- 新建：本目录 `task_plan.md`、`notes.md`、`实施报告.md`。
- 未变更：现有 RWKV 生产工具、配置、启动器、运行制品与路线文档。

## 任务

### 任务 1：供应商源码与许可证

- [ ] 以 `apply_patch` 建立 `vendor/rwkv7_k0_fused/`，保留 Apache-2.0 `LICENSE`、官方原件、专用 C++ 注册文件和 `manifest.json`。
- [ ] 在清单登记官方仓库、固定提交、原路径、原文件 SHA-256、修改说明、编译宏和许可证。
- [ ] 用 `sha256sum` 或 `shasum -a 256` 核验落盘原件与已归档官方 tarball 内文件逐字节一致。

### 任务 2：独立 K0 Python 后端

**产出接口：**

- `load_k0_extension(*, verbose: bool = False) -> Any`：以 `_N_=16`、`_CHUNK_LEN_=16` 加载扩展，校验 CUDA 架构和工具链。
- `rwkv7_k0_fused(r, w_raw, k, v, a, b) -> torch.Tensor`：六输入均为 `[B,128,112]` 连续 CUDA BF16，返回同形 BF16。
- `backend_contract() -> dict[str, Any]`：返回提交、许可证、头宽、通道、长度、dtype、核内状态和源码摘要。

- [ ] 实现全量输入断言，禁止 CPU、FP32/FP16、非连续、形状不符和 `requires_grad` 不一致的静默运行。
- [ ] 用 `torch.autograd.Function` 保存六输入、FP32 分块状态 `s` 和 FP32 `sa`，反向返回六个 BF16 梯度。
- [ ] 扩展缓存位于持久运行根的独立子目录，不写 `/tmp`；本机 `--help` 不触发编译。

### 任务 3：等价性与性能基准

**产出接口：**

- `--phase synthetic`：固定种子构造六个 BF16 输入，比较 FP32 参考、纯 PyTorch BF16 路径和 fused 前向、六输入梯度及一次 AdamW 更新。
- `--phase lspr23-first-batch`：只读冻结 LSPR23 源年首批，以同一 K0/C00 权重比较端到端 logits、损失、全参梯度和一次 AdamW 更新，目标年路径枚举数必须为零。
- `--phase epoch-throughput --backend pytorch|fused`：用冻结 LSPR23 源年、同种子和同权重独立运行 `1000` 个完整优化步，保存吞吐、墙钟、内外峰值显存、选择指标与制品摘要。

- [ ] 将公式对照与真实数据阶段分开；合成数据只裁决实现正确性，不建立 SwanLab 身份或科学结论。
- [ ] 对所有对照输出 `max_abs`、`max_rel`、`rmse`、`reference_scale`、有限值状态和通过/失败。
- [ ] 任一数值、梯度、优化步或选择指标门失败时退出非零，不生成训练授权。

### 任务 4：冻结配置与唯一远程启动器

- [ ] 配置冻结形状、精度、种子、源年数组白名单、批量、步数、误差门、性能及选择一致门、运行根和源码摘要。
- [ ] 启动器仅接受 `synthetic`、`lspr23-first-batch`、`epoch-pytorch`、`epoch-fused`、`all`，默认 `all` 严格顺序执行。
- [ ] 在服务器运行前机械断言 `torch==2.13.0+cu130`、CUDA 13.0、计算能力 `(12,0)`、`nvcc`、`ninja`、空闲资源和输入摘要。
- [ ] 只定义一条服务器基准命令，不在本任务执行、同步或访问服务器。

### 任务 5：验证、报告与提交

- [ ] 运行 `py_compile`、独立模块导入、两个 CLI `--help`、配置核验、`bash -n`、源码与许可证哈希、静态 CUDA 合同扫描、`git diff --check`。
- [ ] 在实施报告记录 Context7 库 ID、可用文档版本、目标版本缺口、文件清单、验证输出、唯一服务器命令、工作量和阻断。
- [ ] 检查共享暂存区，只暂存并提交本任务新文件，回报提交 SHA。

## 门槛依据

- BF16 的单次正常数舍入单位为 `2^-8=0.00390625`；官方前向、反向在核内用 FP32 状态与累加，仅六输入、输出和梯度为 BF16。
- 不根据待测结果调门。初始冻结公式输出和六梯度的相对误差门为 `0.02`（约 `5.12` 个 BF16 舍入单位），绝对误差门为 `0.03125`（`8` 个舍入单位）。
- 模型 logits/损失、全参梯度和一次 AdamW 更新使用同一混合门 `abs <= 0.03125 + 0.02*|reference|`；选择指标要求最佳轮与比较关系完全一致，不以容差替代选择一致性。
- 性能不预注册最低加速比；只有 fused 整轮有效流吞吐不低于纯 PyTorch，且峰值显存不高于纯 PyTorch，才具备工程接入资格；数值门优先于性能门。

## 状态

- [x] 阶段 1：读取规则、技能、恢复链、既有审计、当前 BF16 工具、K0 容量收据合同和官方固定源码。
- [ ] 阶段 2：新增供应商原件、后端、基准、配置和启动器。
- [ ] 阶段 3：本机静态与 CLI 验证，形成实施报告。
- [ ] 阶段 4：只提交独占新文件并交付唯一服务器基准命令。

**当前阶段：** 阶段 2，准备落盘供应商原件和独立后端。

## 阻断项

- Context7 只提供 PyTorch `2.12` 文档索引，未提供目标 `2.13` 条目；因此 `2.13.0+cu130` ABI、`sm_120` 代码生成和 RTX 5090 真实执行保持服务器待证。
- 本任务禁止访问服务器，故不能交付真实等价性、吞吐或显存结果，只能交付可执行的门禁。
