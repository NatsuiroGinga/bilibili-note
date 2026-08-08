# 单私有 LoRA 结构与优化归因证据记录

## Evidence Record

### ER-20260723-asym-full-01

- **Source**：`.Codex/docs/sdd/task-asymmetric-physics-adapter/report.md`
- **Source type**：experiment artifact
- **Supports**：硬任务路由能够保持家族路径完全不变；当前联合目标的单私有 LoRA 显著降低物理误差但损害子类和未知攻击检测。
- **Contradicts**：物理残差下降会自然转化为检测收益。
- **Method / dataset / metric**：Qwen3-1.7B、GeNIS、ns-3、202 步、`eval300`、配对自助法。
- **Limitation**：只有训练随机种子 42；无法单独归因结构、物理梯度、联合损失或学习率。
- **Project relevance**：本诊断实验的直接起点。
- **Claim strength**：strong

### ER-20260722-s3s4-01

- **Source**：`.Codex/docs/sdd/task-s3-s4-detection/report.md`
- **Source type**：experiment artifact
- **Supports**：共享适配器中的物理与生成目标存在任务负迁移，且物理、状态收益与检测收益可以方向相反。
- **Contradicts**：固定权重联合训练已经足够。
- **Method / dataset / metric**：S3/S4、GeNIS、ns-3、同协议 `eval300`。
- **Limitation**：共享适配器结果不能直接证明私有适配器的因果机制。
- **Project relevance**：说明必须控制物理梯度写入位置。
- **Claim strength**：strong

### ER-20260723-asym-literature-01

- **Source**：`.Codex/docs/非对称共享私有多任务适配文献综述.md`
- **Source type**：project note，链接 20 篇可解析全文与结构化笔记
- **Supports**：非对称迁移、共享私有参数和适配器组合具有理论与工程先例；多专家路由存在坍缩、负载与语义捷径风险。
- **Contradicts**：只要隔离参数就必然消除任务负迁移。
- **Method / dataset / metric**：AMTL、共享私有表示、低秩适配、混合专家、物理门控。
- **Limitation**：多数论文不研究生成式恶意流量检测，不能替代本项目实验。
- **Project relevance**：约束允许和禁止的结构性结论。
- **Claim strength**：supported

## 当前证据缺口

1. 缺少生成梯度单独作用于私有 LoRA 的结果。
2. 缺少状态与物理梯度单独作用于私有 LoRA 的结果。
3. 缺少联合目标在非恒定学习率下的结果。
4. 缺少胜出结构的跨训练随机种子证据。

## 已批准范围

- D1、D2、D3 为唯一第一阶段诊断。
- D1 与 D2 仅作因果诊断，不进入最终方法候选。
- 只有 D3 通过全部原门槛才运行种子 43、44。
- 不扫描秩、损失权重、门控、预热比例、峰值学习率、最低学习率或其他调度器。

## 2026-07-23 实现与冒烟验收

- 已实现 `joint_constant`、`generation_only`、`physics_only`、`joint_warmup_cosine` 四种固定模式，旧 D0 默认行为保持兼容。
- 独立复审发现并修复两项重要问题：禁用分支改为同序无梯度前向，避免改变随机失活消耗顺序；评估脚本改为固定模式与正式训练目录绑定，并核验训练摘要和适配器路径。
- 服务器可编辑安装、Python 语法、三个 Shell 语法和唯一新测试文件均通过；精确测试结果为 `6/6`。
- D1 冒烟目录：`runs/asymmetric-physics-diagnostics/qwen3-1.7b-seed42-d1-generation-only-smoke2-v1/`，SwanLab `1e0qiil2`，退出码 `0`。
- D2 冒烟目录：`runs/asymmetric-physics-diagnostics/qwen3-1.7b-seed42-d2-physics-only-smoke2-v1/`，SwanLab `k7de9f01`，退出码 `0`。
- D3 首次三进程并发冒烟因显存不足退出，失败日志保留在 `qwen3-1.7b-seed42-d3-joint-warmup-cosine-smoke2-v1.launcher.log`；根因是三个进程合计占满 31 GiB 显存，不是代码或算法异常。
- D3 单独重跑目录：`runs/asymmetric-physics-diagnostics/qwen3-1.7b-seed42-d3-joint-warmup-cosine-smoke2-v2/`，SwanLab `qflh2r5z`，退出码 `0`。
- 三组生成样本顺序哈希均为 `8caa3c5e66f93f706636dc0a2c838dcdd82dcb8fda685cb5847ec91a032bee1c`，物理样本顺序哈希均为 `3cdfc2837615cc36b4312eaef0417da0efca8d44a03e6e9a7647a608e664cfb4`。
- D1 的状态头梯度、状态损失、物理损失和物理优化样本均为零；D2 的生成损失、生成优化样本、子类样本和令牌均为零；D3 两步学习率为 `2e-5`、`2.9473684210526317e-5`。
- 三组冻结 S3 摘要均未变化，家族关闭私有分支后的 logits 差均为 `0.0`。

## 2026-07-23 正式运行

- D1 训练目录：`runs/asymmetric-physics-diagnostics/qwen3-1.7b-seed42-d1-generation-only-full202-v1/`；`screen` 为 `d1-diag-202`。
- D2 训练目录：`runs/asymmetric-physics-diagnostics/qwen3-1.7b-seed42-d2-physics-only-full202-v1/`；`screen` 为 `d2-diag-202`。
- 两组于 `2026-07-23 11:24` 并行启动。并行时间与吞吐量不用于论文效率比较。
