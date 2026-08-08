# 共享低秩基底的物理状态编码专家实施计划

> **面向实现代理：** 必须使用子代理驱动开发逐任务实现和复审。项目明确禁止测试驱动开发；先按合同实现，再新增合同测试并在服务器运行。

**目标：** 实现同预算单适配器与共享低秩基底物理状态编码专家的种子 42、50 步方向探针，并生成可复核的自动裁决。

**架构：** 冻结 Qwen3-1.7B 与 S3 检测适配器，在第 13 层由冻结状态头产生路由状态，在第 24 至 27 层注入共享秩 16 低秩残差，在最终隐藏状态由可训练状态头接受双锚点和队列守恒监督。两个变体只在全 1 通道码与预测状态驱动的三个固定正交通道码之间不同。

**技术栈：** Python 3.10、PyTorch、Transformers、PEFT、PyYAML、SwanLab、pytest、Black、Ruff、Bash。

**当前执行状态：** 2026-07-24 用户调整优先级后，只执行任务 1 与任务 3 的代码复审部分。任务 2、结果图和实验裁决暂停，待主控冻结未触碰 GeNIS 测试清单和同协议正式基线后再解锁。

## 全局约束

- 只允许种子 `42` 和 `2` 或 `50` 步；不得提供 202 步入口。
- 不扫描秩、层位置、专家数、分位数、码向量、学习率或损失权重。
- 路由只接收模型预测的五维状态及其派生增量，不得接收标签、来源、场景号、队列真值、容量或通量。
- 共享检测适配器冻结，大类门控固定为 `0`。
- 单适配器与路由候选均使用每层 rank `16` 的同一形状 A/B 基底、四个目标层和全部激活参数。
- 正式运行使用服务器 `uv run --no-sync` 与 SwanLab 在线模式。
- 不修改 D0-D3、B0/B1、E1/E2 的实现、配置、入口或历史结果。
- 不修改 `pyproject.toml`；入口使用 `python -m`，避免碰触当前共享脏文件。
- 不提交 Git，不推送。

---

### 任务 1：结构、路由、训练与自动裁决

**文件：**

- 新建：`thesis/experiments/llm_probe/src/flow_probe/physics_routed_experts.py`
- 新建：`thesis/experiments/llm_probe/src/flow_probe/physics_routed_experts_train.py`
- 新建：`thesis/experiments/llm_probe/src/flow_probe/physics_routed_experts_analysis.py`
- 新建：`thesis/experiments/llm_probe/configs/physics_routed_experts_seed42.yaml`
- 新建：`thesis/experiments/llm_probe/scripts/run_physics_routed_experts_probe.sh`
- 新建：`thesis/experiments/llm_probe/tests/test_physics_routed_experts.py`

**接口：**

- `RouteThresholds(growth: float, pressure: float)` 保存固定预测分位数阈值。
- `calibrate_route_thresholds(predicted_state: Tensor) -> RouteThresholds` 只接受 `[N,5]` 预测状态。
- `route_predicted_state(predicted_state: Tensor, thresholds: RouteThresholds) -> Tensor` 返回 `[B]` 的 `0/1/2` 专家编号。
- `hadamard_expert_codes(rank: int = 16) -> Tensor` 返回 `[3,16]` 固定满支持正交码。
- `SharedBasisStateExpert(hidden_size=2048, rank=16, residual_ratio_cap=0.1)` 实现共享 A/B、固定码、零门和显式旁路。
- `PhysicsRoutedExpertRuntime` 提供训练前向、候选前向、自由生成、路由覆盖、专家移除和结构状态保存；底层模型不得注册到结构状态中。
- `train_physics_routed_expert_variant(..., variant: Literal["single", "routed"])` 执行 `2/50` 步固定训练并写完整制品。
- `analyze_physics_routed_experts(single_output, routed_output, output)` 核对样本顺序、预算、路由、专门化和联合收益后写 `comparison_summary.json`。

- [ ] **步骤 1：实现纯数学结构与路由**

  实现输入形状、有限值、非负状态、阈值、码正交性、路由编号、任务掩码、秩与参数预算的强校验。共享 A/B 使用确定性初始化，三专家码和全 1 对照码均为非参数缓冲区。

- [ ] **步骤 2：实现三路径运行时**

  复用既有 Qwen 第 13、24、25、26、27 层挂钩约定，但新增最终隐藏状态预测头。训练、自由生成和候选评分均必须通过相同路由结构；大类逐行掩码不得注入残差；显式旁路必须恢复冻结 S3。

- [ ] **步骤 3：实现固定训练器与制品合同**

  复用 `PhysicsTrainingSettings`、样本调度、双锚点掩码和 `queue_balance_residual`。两个变体使用相同样本顺序、优化器、初始化和验证集。保存路由允许/拒绝字段、阈值、码内积、每步专家梯度与参数更新、家族等价性、验证使用率、条件损失矩阵和专家移除结果。

- [ ] **步骤 4：实现比较与停止规则**

  比较程序必须拒绝不同输入哈希、不同样本顺序、不同 rank、不同参数量或不同激活参数量。逐项判定无泄漏、使用熵、无坍缩、三专家非零更新、对角专门化、家族等价、子类损失和物理指标，只有全部通过才令 `overall_pass=true`。

- [ ] **步骤 5：新增固定配置与包装器**

  配置固定现有生成/物理文件、种子 42、rank 16、学习率 `2e-4`、双锚点、损失权重 `1.0/0.01`、SwanLab 在线项目。包装器只接受 `single|routed`、唯一输出目录和 `2|50`，固定模型与 S3 路径，使用 `uv run --no-sync python -m`，拒绝覆盖。

- [ ] **步骤 6：实现后新增合同测试**

  测试至少覆盖：码形状/满支持/两两内积为零；阈值校准只需预测状态；三路由规则；候选与对照参数量/秩/激活参数相同；家族掩码恒等；路由不接受元数据；专家覆盖与移除；分析器对每个失败门槛均返回失败。

- [ ] **步骤 7：本地只做静态交付检查**

  运行 `black` 处理三个 Python 源文件和一个测试文件，运行 `ruff check`、`bash -n`、YAML 解析和 `git diff --check`。不得在本机运行 pytest。

### 任务 2：服务器最小验证与唯一方向探针

**制品目录：**

- 冒烟单适配器：`runs/physics-routed-experts/qwen3-1.7b-seed42-shared-basis-single-r16-smoke2-v1/`
- 冒烟路由候选：`runs/physics-routed-experts/qwen3-1.7b-seed42-shared-basis-routed-r16-smoke2-v1/`
- 50 步单适配器：`runs/physics-routed-experts/qwen3-1.7b-seed42-shared-basis-single-r16-full50-v1/`
- 50 步路由候选：`runs/physics-routed-experts/qwen3-1.7b-seed42-shared-basis-routed-r16-full50-v1/`
- 比较裁决：`runs/physics-routed-experts-comparison/qwen3-1.7b-seed42-shared-basis-r16-full50-v1/`

- [ ] **步骤 1：增量同步白名单文件**

  从本地实验根使用 `rsync -avR` 同步六个新增文件，不带 `--delete`，排除 `.venv`、`runs`、模型、缓存和凭据；服务端核对文件存在与 SHA-256。

- [ ] **步骤 2：运行最小服务器测试**

  执行：

  ```bash
  uv run --no-sync pytest tests/test_physics_routed_experts.py -q
  ```

  预期：全部通过，无跳过。

- [ ] **步骤 3：运行两个两步真实模型冒烟**

  顺序执行单适配器和路由候选。两个冒烟必须通过零门等价、家族门控、冻结摘要、生成与物理梯度、三路径结构调用、参数预算、SwanLab 制品和输出完整性。

- [ ] **步骤 4：运行唯一两个 50 步对照**

  两步均通过后，顺序运行同预算单适配器和路由候选。若与主进程任务并发，允许等待 GPU；若实际并发，不使用时间、吞吐或显存作比较结论。

- [ ] **步骤 5：运行自动比较**

  执行分析入口，保存逐项门槛和 `overall_pass`。不得在看到结果后改变任何门槛或重新训练。

- [ ] **步骤 6：复核服务器与 SwanLab 制品**

  核对退出码、日志、GPU 错误、运行编号、云端指标点、结构权重、摘要和清单；将核心结果增量回收到本地同相对路径并核对 SHA-256。

### 任务 3：独立复审、图件和研究裁决

- [ ] **步骤 1：独立复审规格与代码质量**

  新审查子代理读取本计划、实现报告和完整新增文件，检查预算数学、路由泄漏、梯度路径、家族保护、指标实现和测试证据。严重或重要问题必须由修复子代理最小修复后重新审查。

- [ ] **步骤 2：生成真实结果图**

  只从比较制品生成专家使用率、条件损失矩阵与同预算相对变化图；保留 Python 可编辑源。经数值和标注核验后，最终图放入 `thesis/figures/第三章/`，文件名采用“图3-X-中文主题”。若结果不值得进入正文，只保留运行目录图，不强行复制到章节目录。

- [ ] **步骤 3：写最终报告并更新总控**

  在本任务目录记录实现、命令、SwanLab、服务端和本地路径、指标、失败边界与裁决。确定结果写回 `output/第一创新点实验总控.md`；只有第二支柱或章节边界发生变化时才更新 `output/开题改进交接文档.md`。
