# R2 因果多窗口物理旁路修复实施计划

> **代理执行要求：** 使用 `subagent-driven-development` 按任务顺序实现；禁止使用 `test-driven-development`。独立复审与实验并行，不得阻塞已经通过运行时门禁的正式运行。

**目标：** 将已失败的静态 18 维物理旁路替换为严格因果的多窗口物理序列，并用等信息量原始历史基线证明增益是否来自物理建模。

**架构：** 从冻结的 TQH-C2 开发训练 `2,048` 条和开发验证 `512` 条逐包被动观测构造固定长度因果窗口。物理分支和原始历史分支使用同形状、同参数预算的轻量时序编码器；物理表示通过零初始化、幅度有界的残差门控进入 DistilBERT 表征。每个种子、每个组使用独立 Python 进程和独立 SwanLab 运行，避免 SwanLab `0.9.0` 的进程内多运行会话复用问题。

**技术栈：** Python 3.10、PyTorch、Transformers、PyArrow、YAML、SwanLab 0.9.0、Bash、uv。

## 全局约束

- 当前任务是唯一一次多窗口修复分支，不再增加第二轮结构或超参数补救。
- 仅使用冻结开发训练与开发验证；`final_test_visible=false` 必须由运行时断言强制。
- 不改变样本 ID、标签、划分、文本输入、基础模型、种子 `42/43/44`、训练轮数、优化器、学习率或总优化步预算。
- 所有窗口严格因果，只使用当前包及此前包；不得读取攻击名称、采集单元编号、场景编号、最终标签派生字段或未来包。
- 真实、置换和随机旁路必须保持相同张量形状、编码器结构、参数量和训练预算。
- 增加等信息量原始历史基线，区分“历史信息增益”和“物理变换增益”。
- 物理残差注入必须零初始化、幅度有界，并记录实际门控幅度；不得用无界相加破坏基础表征。
- 不运行独立 GPU 冒烟、独立目标测试、AST 检查、Prettier 或重复 Pyright/Ruff；语义门禁并入正式入口。
- 任何最终裁决必须报告全部预注册种子，不挑选最好种子。

---

## 任务 1：冻结多窗口数据合同与诊断假设

**文件：**

- 创建：`.Codex/docs/sdd/task-r2-multiwindow-sidecar-repair/data_contract.md`
- 更新：`.Codex/docs/sdd/task-r2-multiwindow-sidecar-repair/implementation_plan.md`

**输入：** 当前静态旁路制品、逐包观测、架构规格与数据可行性审计。

**输出：** 唯一字段白名单、窗口边界、张量形状、归一化统计来源、置换分层键、随机生成统计来源和数据 SHA-256 合同。

- [x] 记录 `T-A=0`、`T-H=等信息量原始历史`、`T-P=真实物理序列`、`T-S=同来源同传输族同划分整段置换`、`T-R=仅从开发训练统计生成随机序列` 的固定语义。
- [x] 将窗口限定为逐包被动可观测字段；所有归一化参数只从开发训练计算。
- [x] 登记逐样本包顺序、截断/填充、缺失掩码和 `sample_id` 一一对应门禁。
- [x] 明确当前 TQH-C2 无隐藏队列真值，因此本修复只裁决开发检测增量，不伪造物理状态误差。

## 任务 2：实现确定性多窗口派生器

**文件：**

- 创建：`thesis/experiments/llm_probe/src/flow_probe/r2_multiwindow_sidecar.py`
- 创建：`thesis/experiments/llm_probe/configs/r2_multiwindow_sidecar_materialization_v1.yaml`
- 创建：`thesis/experiments/llm_probe/scripts/run_r2_multiwindow_sidecar_materialization.sh`
- 创建：`.Codex/docs/sdd/task-r2-multiwindow-sidecar-repair/materialization_report.md`

**接口：**

- `build_causal_packet_history(...) -> pyarrow.Table`
- `derive_physics_sequence(...) -> pyarrow.Table`
- `derive_raw_history_sequence(...) -> pyarrow.Table`
- `validate_multiwindow_artifact(...) -> dict[str, object]`

**输出制品：**

- `runs/r2-physics-sidecar-pilot/inputs/tqhc2-multiwindow-v1/detection-view.parquet`
- `runs/r2-physics-sidecar-pilot/inputs/tqhc2-multiwindow-v1/raw-history.parquet`
- `runs/r2-physics-sidecar-pilot/inputs/tqhc2-multiwindow-v1/physics-history.parquet`
- `runs/r2-physics-sidecar-pilot/inputs/tqhc2-multiwindow-v1/input-summary.json`
- `runs/r2-physics-sidecar-pilot/inputs/tqhc2-multiwindow-v1/artifact-manifest.json`

- [ ] 流式读取冻结逐包观测，只保留合同中的 `2,560` 个开发样本。
- [ ] 按 `sample_id` 与包序号恢复严格因果顺序，构造固定窗口、有效长度和缺失掩码。
- [ ] 从同一原始历史生成等信息量原始序列与物理变换序列，禁止额外未来信息。
- [ ] 正式入口运行时检查行数、唯一 ID、顺序、标签隔离、训练统计来源和制品 SHA-256。
- [ ] 探索性派生只运行一次；记录模式、行数、语义摘要、耗时和空间，不执行逐字节双物化。

## 任务 3：实现多窗口编码与有界残差注入

**文件：**

- 创建：`thesis/experiments/llm_probe/src/flow_probe/r2_multiwindow_fusion.py`
- 修改：`thesis/experiments/llm_probe/src/flow_probe/r2_distilbert_sidecar_probe.py`
- 更新：`.Codex/docs/sdd/task-r2-multiwindow-sidecar-repair/implementation_report.md`

**接口：**

- `CausalWindowEncoder.forward(sequence, valid_mask) -> encoded_state`
- `BoundedResidualFusion.forward(hidden_state, encoded_state, uncertainty) -> fused_hidden_state`
- 命令行增加 `--variant T-A|T-H|T-P|T-S|T-R`，每次进程只执行一个组。

- [ ] 使用相同编码器规格处理 `T-H/T-P/T-S/T-R`；`T-A` 保留同形状零输入和关闭门控。
- [ ] 融合形式固定为 `h_fused = h + alpha * gate * projected_state`；`alpha` 零初始化并通过有界函数限制幅度。
- [ ] 记录 `alpha`、门控均值/分位数、编码范数和融合扰动范数，定位物理分支是否压倒基础表征。
- [ ] 单组完成后保存独立指标、预测、模型、收尾收据和制品清单；禁止在同一进程创建第二个 SwanLab 运行。
- [ ] 保留旧静态探针读取能力，只读历史结果；新修复使用独立输出根和配置模式，禁止覆盖旧制品。

## 任务 4：实现单组独立进程启动器与配置

**文件：**

- 创建：`thesis/experiments/llm_probe/configs/r2_distilbert_multiwindow_seed42.yaml`
- 创建：`thesis/experiments/llm_probe/configs/r2_distilbert_multiwindow_seed43.yaml`
- 创建：`thesis/experiments/llm_probe/configs/r2_distilbert_multiwindow_seed44.yaml`
- 创建：`thesis/experiments/llm_probe/scripts/run_r2_distilbert_multiwindow_probe.sh`

**输出根：** `runs/r2-transformer-sidecar-probe/distilbert-multiwindow-v1/`

- [ ] 启动器按 `42→43→44`、每种子 `T-A→T-H→T-P→T-S→T-R` 顺序启动独立 Python 进程。
- [ ] 已完成组经绑定和制品清单校验后跳过；失败组保留证据并停止，不自动覆盖。
- [ ] 五组均完成后才生成种子汇总；十五组均完成后才允许离线裁决。
- [ ] 每组使用 SwanLab 在线项目 `mortiswang/malicious-traffic-llm`，动态标签长度运行时检查不超过 20 个字符。
- [ ] 检查点间隔不超过 20 步，状态和日志可跨服务器重启恢复。

## 任务 5：最小验证、独立复审与正式运行

**文件：**

- 创建：`.Codex/docs/sdd/task-r2-multiwindow-sidecar-repair/review_report.md`
- 创建：`.Codex/docs/sdd/task-r2-multiwindow-sidecar-repair/run_progress.md`

- [ ] 实现代理只执行一次精确范围 Python 语法检查和一次修改后 Shell `bash -n`；不运行独立训练冒烟或目标测试。
- [ ] 新审查代理核对数据泄漏、因果窗口、同信息预算、张量形状、零初始化门控、单组进程和可恢复运行。
- [ ] 复审与正式运行并行；若发现影响结果有效性的严重或重要问题，立即停止并作废受影响结果。
- [ ] 正式入口的运行时断言通过后，运行十五组开发实验并完整登记 SwanLab、本地日志、预测和制品哈希。

## 任务 6：统计分析与唯一裁决

**文件：**

- 创建：`thesis/experiments/llm_probe/src/flow_probe/r2_multiwindow_analysis.py`
- 创建：`.Codex/docs/sdd/task-r2-multiwindow-sidecar-repair/final_report.md`
- 更新：`output/第一创新点实验总控.md`

- [ ] 在每个种子计算 `P-A`、`P-H`、`P-S`、`P-R` 的宏平均 F1 配对差值及分层自助法 95% 区间。
- [ ] 同时报告良性误报率、攻击召回率、Brier 分数、期望校准误差、运行时间和峰值显存。
- [ ] 只有真实物理序列相对基础、等信息量历史、置换和随机对照形成预注册一致优势，才允许进入完整 R2/Qwen。
- [ ] 若真实物理序列仍未优于对照，停止当前 R2 检测增益路径；只允许保留已由 ns-3 支持的物理一致性结论，不再进行第二次补救。

## 当前状态

- [x] 静态旁路失败信号已出现：种子 42 `T-P` 宏平均 F1 `0.612710`，低于 `T-A` 的 `0.792742`。
- [x] `T-S` 宏平均 F1 `0.784414`，接近 `T-A`，初步指向样本特定物理表示或注入方式，而不是仅由额外参数造成。
- [x] 唯一多窗口修复边界已预注册。
- [x] 架构规格与数据可行性审计已经完成。
- [x] 本地输入可行性已核验：冻结开发集共 `2,560` 个样本，对应 `173,196` 个逐包观测，足以构造一次因果多窗口开发物化。
- [x] 窗口边界固定为 `[0,2)`、`[2,4)`、`[4,8)`、`[8,N_decision)`；不得把静态向量复制为四窗口，也不得使用决策时点之后的数据。
- [x] 已定位旧 `T-P` 路由缺陷：`92` 条应为 `UNKNOWN` 的 UDP 承载流被送入 UDP 专家。修复后只使用部署时可观测证据路由，`UNKNOWN` 固定走 `shared_only`。
- [x] 缩放与融合边界已冻结：禁止未来全局尺度；ns-3 物理真值尺度与 TQH 模型输入尺度分离；残差融合零初始化并限制最大相对幅度为 `10%`。
- [x] 对照增加 `T-H` 等信息量原始历史，且每个实验组使用独立 Python 进程，规避 SwanLab `0.9.0` 同进程第二次初始化故障。
- [ ] 任务 1 数据合同仍在编写，**尚未冻结**；不得把进行中状态写成完成事实。
- [ ] 任务 2 必须等待数据合同冻结后开始；服务器无 GPU 不阻塞本机数据合同、物化器和融合代码实现。

### 静态探针补充进度（2026-08-04）

- 种子 42 的 `T-A/T-P/T-S/T-R` 已全部完成，宏平均 F1 分别为 `0.7927419192/0.6127103249/0.7844144907/0.7875604671`。静态实现的严格门槛已因 `T-P<T-A` 无法通过。
- 种子 43 的 `T-A/T-P` 已完成，宏平均 F1 分别为 `0.8010245540/0.7989545883`；`T-S` 在第 0 步因 SwanLab `401` 失败，`T-R` 未开始；种子 44 未开始。
- 服务器当前以无卡模式运行，CUDA 不可用且无 `screen` 会话。静态剩余训练等待 GPU，但多窗口修复的无卡实现继续推进。
- 上述静态结果不能否决完整 R2；本计划是唯一一次允许的结构修复，完成后不再追加第二轮补救。
