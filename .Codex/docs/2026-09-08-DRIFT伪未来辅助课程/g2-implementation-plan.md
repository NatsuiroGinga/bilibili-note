# N12 G2 严格 family 隔离梯度与短步确认实施计划

> **实施代理必读：** 必须使用 `superpowers:subagent-driven-development` 与 `daily-coding` 逐任务实施；同一时刻只允许一个实现代理修改下列文件。不得运行 `black`、人工夹具、单元测试或集成测试。

**目标：** 实现并运行一个 `screening_only` 的 N12 G2 真实数据诊断，在两个互补 T17 family 严格隔离折上完成逐任务梯度、七个同预算短步臂和确定性 family 打乱负控，输出是否仅可进入两个反馈块活动探针的裁决。

**实现方式：** 单一 Python 入口负责身份核验、family 映射与折构造、折内分词器和预训练端点重建、探针、梯度、七臂短步、负控、恢复及结果发布。G0/G1 只作为已闭合谱系、实现语义和 G2 准入门；因二者读取过全 T17，严禁把 G0 权重、G1 梯度、P0 全 T17 分词器或探针直接用于严格隔离折。

**技术栈：** Python 3.14、PyTorch、PyArrow、Hugging Face `tokenizers`、JSON、Bash、既有远程启动与回传入口。

**规范：** `thesis/methods/第三章-DRIFT伪未来辅助任务课程研究卡.md` 第 5.2、7.3、7.4、7.5 节。

## 全局约束

- 只允许访问配置显式列出的 T17 `train/val` eSLD 文件和 T17 raw DGA family 文件；配置、路径、递归字符串值和运行时已解析路径中出现 `T18`–`T25` 即在读数据前失败。
- 数据 revision 固定为 `3b31077020cd1c013d0a75cad51042a2327c4521`；五个输入文件及 SHA-256 复用 G1 配置，不重新发现成员。
- G1 必须同时满足 `status=completed`、结果/检查点/状态哈希闭合、`g1_verdict=eligible_for_g2_only`；这只批准 G2，不证明局部迁移伤害、负迁移、课程或跨年效果。
- 冻结种子 `42`、batch `1024`、Adam、学习率 `1e-4`、梯度裁剪 `1.0`、一遍拟合成员、MTP 遮蔽率 `0.15`、TOV 打乱概率 `0.5`、`ignore_index=-100`、字符长度 `77`、子词长度 `30`、字符词表 `43`、子词词表上限 `30522`、dropout `0.1`、ECE `15` 个等宽概率箱，均复用 P0/G0 已登记数值；不得按 G1/G2 结果调整。
- 短步窗口固定为每臂 `32` 批、`32,768` 个拟合侧源样本；这是 P0/G0 的既有单个 I/O 块。每折在任何指标计算前冻结该折确定性拟合迭代器的首个完整块及有序成员摘要，所有臂和两个分支复用同一块，不按结果另选。
- `source_fpr=0.01` 只复用 P0 的筛选口径：阈值在每折拟合侧良性分数上按并列概率组整体冻结，再在元验证侧重计数；不得称正式部署预算。
- 使用 `cuda-bf16-amp-fp32-sensitive-v1`；参数、优化器、损失、归一化、梯度组合和指标保持 FP32，BF16 只用于 CUDA 前向。资源收据记录实际设备、TF32 开关、精度、峰值显存、吞吐、墙钟与检查点大小。
- 不实现 PF-FAC、两个反馈块、完整课程、T18/T19 止损、N13/N14、条件键路由或任何联合机制。G2 最强成功状态只能是 `eligible_for_two_block_activity_probe_only`。

## 文件与制品

实施时只新增：

- `thesis/experiments/llm_probe/tools/ch3_drift_n12_g2_family_isolated_short_step.py`
- `thesis/experiments/llm_probe/configs/ch3-drift-n12-g2-family-isolated-short-step-v1.json`
- `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_drift_n12_g2_family_isolated_short_step_v1.sh`
- `.Codex/docs/2026-09-08-DRIFT伪未来辅助课程/g2-implementation-report.md`

真实运行目录固定为 `thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-n12-g2-family-isolated-short-step-v1/`，原子发布：

- `effective-config.json`：解析后的配置与代码、数据、G0/G1/P0 身份。
- `fold-manifest.json`：family 集、train-only/val-only 集、计数、互斥检查、成员顺序摘要、折与负控哈希；不保存原始域名。
- `fold-0/tokenizer.json`、`fold-1/tokenizer.json`：仅由该折拟合侧训练的 WordPiece 分词器。
- `checkpoint.pt`：唯一可恢复工作状态；每 32 个 I/O 批次和每个短步臂完成后原子覆盖。
- `arms/<fold>-<branch>-<arm>.json`：已完成臂的指标、梯度、模型哈希和资源收据；使恢复时不重跑已完成臂。
- `result.json`：两折、两分支、七臂、真实/打乱 family、固定/重拟合探针指标与科学裁决。
- `manifest.json`：除自身与可变 `status.json` 外的上述文件，以及脚本、配置、启动器、输入、G0/G1 制品的 SHA-256、字节数和语义角色；避免自引用哈希。
- `status.json`：`running/completed/failed`、当前阶段、折、分支、臂、结果/检查点/manifest 哈希和原始错误类型。
- `run.log`：阶段心跳与原始退出码；不得记录域名、凭据或私有连接值。

## 冻结接口

入口参数固定为：

```text
--config PATH --project-root PATH --run-dir PATH [--resume]
```

核心接口在同一脚本内实现，不新建通用框架：

| 函数 | 输入 | 输出 |
| --- | --- | --- |
| `verify_predecessors` | `Mapping[str, Any]`, `Path` | `dict[str, Any]` |
| `build_family_mapping` | `Mapping[str, Any]`, `Path` | `FamilyMapping` |
| `build_complementary_folds` | `FamilyMapping` | `tuple[FoldSpec, FoldSpec]` |
| `build_shuffled_labels` | `Sequence[MetaRow]`, `config_sha256: str` | `ShuffledLabels` |
| `train_fold_endpoint` | `FoldSpec`, `branch: str`、可空恢复状态 | `EndpointReceipt` |
| `train_frozen_encoder_probe` | `FoldSpec`、端点映射、可空恢复状态 | `ProbeReceipt` |
| `compute_fold_gradients` | `FoldSpec`、分支、端点、探针 | `GradientReceipt` |
| `run_short_step_arm` | `FoldSpec`、分支、臂、端点、`BlockSpec` | `ArmReceipt` |
| `evaluate_arm` | `ArmReceipt`、探针模式、family 模式 | `MetricReceipt` |
| `adjudicate_g2` | 完整结果映射 | 裁决状态字符串 |

`FamilyMapping` 至少包含规范 eSLD SHA-256、唯一 family、train/val 角色与歧义状态；`FoldSpec` 包含拟合/元验证 family、train-only/val-only family、良性角色、成员数和有序摘要；`ArmReceipt` 必须绑定起点模型、起点优化器、固定成员块、终点模型和 32 步完成状态。

## 折与负控的唯一构造

1. 以 G1 的 `raw_to_esld` 语义把 T17 raw DGA 连接到 T17 train/val DGA eSLD；同一 eSLD 对应 family 集大小为 1 才可用，大小大于 1 的歧义键从 family 梯度、分折、短步和主裁决全部排除，缺失键令数据门失败。
2. 取 train 与 val 共同出现的 family，按 T17 train 可用样本支持量降序排序；支持量相同按规范 family 名的 UTF-8 字节序。依次放入当前累计 DGA 样本数较小的 family 集，相等固定放入 `F0`。
3. 折 0 以 `F0` 拟合、`F1` 元验证；折 1 交换。train-only family 在两折均只进入拟合侧；val-only family 在两折均只进入元验证附件且不得参与跨折主裁决。全部良性 T17 train 只拟合，全部良性 T17 val 只元验证，不重采样。
4. 每个 family 的全部 eSLD 必须同侧；train/val 任一规范 eSLD 重复时从拟合侧移除并在 manifest 记录。若移除后仍重叠、任一折少于两个共享 family、拟合或元验证为空，则工程无效。
5. 每折 WordPiece 分词器、字符/子词等权三任务预训练、统计和检测探针只读拟合侧。模型按 P0 结构和种子 42 重新初始化，按 G0 的一遍成员与任务语义重训；字符完成后的 RNG 状态按 G0 顺序传给子词。全 T17 G0 权重、G1 梯度和 P0 tokenizer 仅核身份，不装载。
6. 对每折元验证 DGA eSLD 按规范 eSLD SHA-256 排序，令 `N` 为行数，计算 `o=1+int(config_sha256[0:8],16) mod (N-1)`，把原 family 标签序列循环移动 `o` 位。`N<2` 失败；每配置只生成一次，须断言样本数和 family 频数逐值保持、eSLD-family 对应已改变。
7. 打乱标签只替换元验证的 family 聚合，不改变折、训练成员、端点、探针、短步成员或概率；真实与打乱评价必须来自同一预测向量。

## 七臂与短步语义

每个 `fold × branch` 从同一折内等权三任务端点、同一 Adam 状态、同一 RNG 和同一 32,768 成员块独立分叉；短步只更新该分支共享编码器，辅助头与检测探针冻结，以隔离表示方向。每臂恰好消费 32 批；六个更新臂各执行 32 次优化器步，`no_update` 执行 0 次，不延长、不早停：

| 键 | 损失或方向 | 用途 |
| --- | --- | --- |
| `no_update` | 不调用 `optimizer.step()`，但完整消费并登记同一块 | 排除评价与探针重算波动 |
| `mtp_only` | 原 MTP 标量损失 | 单任务方向 |
| `tpp_only` | 原 TPP 标量损失 | 单任务方向，不预设有害 |
| `tov_only` | 原 TOV 标量损失 | 单任务方向 |
| `mtp_tov_equal` | `MTP + TOV` | DRIFT 公开固定组合 |
| `all_equal` | `MTP + TPP + TOV` | G0 来源基线 |
| `all_unit_norm` | 每批分别求三个共享编码器梯度，FP32 单位化后相加，再执行共同裁剪 | 范数失衡诊断，不作最终模型 |

除 `all_unit_norm` 外不重标单任务或组合损失；所有更新臂统一在组合后执行 `clip_grad_norm_=1.0`。每臂报告每步任务有效监督数、原始范数、成对余弦、风险方向、裁剪前后范数、损失、更新量、起止模型哈希；任一非有限、零有效监督、成员/步数偏离即工程无效。

每臂短步后执行两套评价：

- `frozen_probe`：复用短步前冻结探针，作为一阶延续与 G2 主裁决。
- `refit_probe_attachment`：编码器冻结，从同一探针初始化和种子在拟合侧按 G1 同规格重拟合一遍，仅作表示敏感性附件，不改变主裁决。

两套均完整报告良性 BCE、DGA micro BCE、真实与打乱 family-macro BCE、默认 FPR/FNR、Recall、Precision、AP、AUROC、拟合侧冻结 1% FPR 阈值下的 TPR/FPR、Brier、ECE；共享 held-out family 是跨折主结果，val-only family 单列。

## 恢复模式

- 阶段顺序固定为 `verify → family_mapping → folds → fold_tokenizer → fold_pretrain_char → fold_pretrain_subword → probe → gradients → arms → adjudicate → completed`。
- `checkpoint.pt` 保存配置/脚本/输入/G0/G1 哈希、阶段游标、折与负控摘要、分词器哈希、模型/优化器/RNG、有效监督累计、固定块摘要、已完成臂索引和结果哈希；每 32 个 I/O 批次及每臂完成后用 `.partial` 原子替换。
- `--resume` 先重算全部权威哈希和折语义哈希；任一漂移即失败并保留旧制品。已存在且哈希闭合的 arm 收据跳过，未闭合臂从共同端点重启，不从半臂权重续接。
- 无 `--resume` 且运行目录已有有效状态时拒绝覆盖。失败写 `status.json` 并保留检查点、日志和原退出码；禁止删除或重跑已完成折来改变负控。

## 科学停止条件

按冻结探针主结果机械裁决，顺序短路：

1. **任务方向门：** 至少一个相同 `branch × task × risk` 在两个互补折均有单位范数 `a<0`，且同一 `branch × risk` 的另一任务在两折均 `a>=0`；否则 `rejected_after_g2_no_stable_direction`。
2. **真实短步门：** 上述有害方向对应的单任务臂须在两折都使同一风险相对 `no_update` 上升，并且另一侧没有形成非支配收益；若一升一降只记恶意-良性取舍，输出 `rejected_after_g2_no_local_harm`。
3. **family 特异性门：** 真实 family 下三个单任务的严格次序须跨折一致并优于保持组大小的打乱次序；相同次序被打乱复现、差异仅由单一 family、支持量二分或 eSLD 长度二分解释，均输出 `rejected_after_g2_no_family_specificity`。二分边界只用 T17 train 的数据中位数，连值整体同侧，不看模型结果。
4. **等权可改进门：** 至少一个同预算更新臂在两折都于 `(R_+,R_-)` 上支配 `all_equal`，或在 `R_-` 不增加时降低 `R_+`；否则 `rejected_after_g2_equal_not_improvable`。
5. **运营披露门：** 所列判别、排序、低误报与校准指标任何一项缺失、非有限或被选择性省略，输出 `invalid_g2_metrics`，不作科学否决。

仅 1–5 全过时输出 `eligible_for_two_block_activity_probe_only`。该状态仍不证明动态权重必要、PF-FAC 有效或课程有效；下一阶段必须另行实施研究卡第 7.5(5) 的两个连续反馈块，G2 入口不得自动启动。

## 实施任务

### 任务 1：冻结配置与身份门

**文件：** 创建配置与 Python 入口骨架。

- [ ] 写入上述全部 G0/G1/P0、五个 T17 输入、数值、精度、七臂和禁止年份合同；G1 固定哈希为：配置 `a8684e2891aeda50ad3e312ab6220df68df2b3e41840e194425cb64dab66116a`、脚本 `35d1300622c61cb692d715c70b0fbd17924f28520b55932ee68e548bb2f57612`、结果 `8a442d87ac2453f6eae71458fcd52391e6cf06e7fd71d6ad400893a89d530360`、检查点 `0dd2adb94ca639f57e0ec270d0dbda7f1270db212b55e59b6c1128c9f4bd9b8a`、状态 `21e74879a876029d9c8a4fd849dcef8a20576493261d7b4a11998d2166d25850`。
- [ ] 固定 G0 配置 `85f19d44be6a646df85c34daba7ff93390f5d997281ed06b419992459ec07ce5`、冻结运行源码 `43601c2229bae12efc0185f72083df6951ee55092b41802ea9e4c5378c5bc68d`、字符结果/检查点 `1815b8e81289df2dd613ab640d49413d378afb1518344378c7b60aa422e17c71`/`70f195ff8048b450772f1d95a8913cc4633e52aca03cde0d621859451fb630a1`、子词结果/检查点 `d8ddb63a94d107facd0ab6c910cf560bf46f798cda071406067b1fb1d949db2d`/`1c4b931ff85d26cc2b517e21e2b1a821424b3089cec9d7513b4785c1f83c951c`；固定 P0 配置/源码 `eab95b6539fa920aa4b929203f3ef81eaf11fa53335e00f367bd9615fce64fcf`/`92056fd37cb9c195d1952b59280101d8c1b9f0a622453ec9c929d378f9c85674`。
- [ ] 实现 `load_config`、递归未来年份拒绝、文件 SHA-256、G0/G1 状态与解释边界核验；在创建运行目录和读 Parquet 前完成。
- [ ] 验证：`jq empty configs/ch3-drift-n12-g2-family-isolated-short-step-v1.json`，再运行 `--help` 和只加载配置的导入检查；不得运行真实数据。

### 任务 2：实现 family 映射、互补折和负控

**文件：** 修改同一 Python 入口。

- [ ] 实现 `FamilyMapping`、`FoldSpec`、唯一 family 连接、歧义排除、最长处理时间优先式平衡、train-only/val-only 角色、eSLD 去重与互斥断言。
- [ ] 在任何模型指标前发布 `fold-manifest.json`，包含 family 明文集合、计数和哈希，但不保存域名；同一 manifest 供恢复与所有臂复用。
- [ ] 实现单次循环移位负控，断言频数保持且对应改变；真实/打乱共享预测。
- [ ] 验证：运行配置导入与 CLI 检查；真实折构造只允许随正式 G2 入口执行，不另建探针脚本或测试夹具。

### 任务 3：实现折内端点、梯度、七臂与恢复

**文件：** 修改同一 Python 入口。

- [ ] 按每折拟合侧训练 tokenizer，按 G0 顺序重建字符/子词等权端点和冻结编码器探针；保存 tokenizer、模型/优化器/RNG 与身份哈希。
- [ ] 计算真实/打乱 family 风险梯度、任务梯度、原始点积、范数、余弦和单位方向；冻结首个 32 批成员摘要。
- [ ] 从同一端点逐臂运行七臂，完成固定与重拟合探针全指标；每臂原子收据后才标完成。
- [ ] 实现阶段式 `checkpoint.pt`、`--resume`、失败保留、manifest 与五种裁决状态；运行身份不自动进入后续阶段。
- [ ] 验证：`py_compile`、`--help`、配置导入；根据实验规则不运行 pytest、不创建合成或抽样数据。

### 任务 4：远程启动、真实短步与实现报告

**文件：** 创建远程启动器与实现报告。

- [ ] 启动器只调用 `scripts/remote_launchers/launch_run_with_pull.sh`，先同步明确文件，再以服务器 `source tools/env/activate.sh` 与 `uv run --no-sync` 启动；传递 `--resume`，保留 Python 与 `tee` 原退出码。
- [ ] 运行前集中执行下列验收命令；通过后才由主代理启动唯一 G2 真实运行。运行完成后核对服务端与本机 `status/result/manifest/checkpoint/arms` 哈希闭合及 SwanLab/日志身份。
- [ ] 报告只写实现、真实运行制品和裁决边界；禁止把 `eligible_for_two_block_activity_probe_only` 写成课程有效。

## 验收命令

```bash
cd thesis/experiments/llm_probe
/opt/miniconda3/envs/rwkv/bin/python -m py_compile tools/ch3_drift_n12_g2_family_isolated_short_step.py
/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_n12_g2_family_isolated_short_step.py --help
/opt/miniconda3/envs/rwkv/bin/python -c "import sys; sys.path.insert(0, 'tools'); import ch3_drift_n12_g2_family_isolated_short_step as g2; print(g2.SCHEMA_VERSION)"
jq empty configs/ch3-drift-n12-g2-family-isolated-short-step-v1.json
bash -n scripts/remote_launchers/run_ch3_drift_n12_g2_family_isolated_short_step_v1.sh
git diff --check -- tools/ch3_drift_n12_g2_family_isolated_short_step.py configs/ch3-drift-n12-g2-family-isolated-short-step-v1.json scripts/remote_launchers/run_ch3_drift_n12_g2_family_isolated_short_step_v1.sh ../../../.Codex/docs/2026-09-08-DRIFT伪未来辅助课程/g2-implementation-report.md
```

真实运行完成后的最小验收：

```bash
jq -e '.status == "completed" and .screening_only == true and (.g2_verdict == "eligible_for_two_block_activity_probe_only" or (.g2_verdict | startswith("rejected_after_g2_")) or .g2_verdict == "invalid_g2_metrics")' runs/diagnostics/ch3-drift-n12-g2-family-isolated-short-step-v1/result.json
jq -e '.status == "completed" and .result_sha256 and .checkpoint_sha256 and .manifest_sha256' runs/diagnostics/ch3-drift-n12-g2-family-isolated-short-step-v1/status.json
jq -e '.forbidden_years_accessed == [] and .folds[0].fit_meta_overlap == 0 and .folds[1].fit_meta_overlap == 0 and .short_step.samples == 32768 and .short_step.batches == 32' runs/diagnostics/ch3-drift-n12-g2-family-isolated-short-step-v1/result.json
```

## 实施边界

- 实施代理不修改恢复卡、路线总控、研究卡、G0/G1/P0 文件或既有运行制品，不暂存、提交、回滚他人改动。
- 静态验证通过只表示入口可运行；只有上述唯一真实 T17 G2 运行的哈希闭合制品才可支持科学停止门。
- 若严格 tokenizer/端点隔离、32,768 成员块或原子恢复任一无法成立，应保留失败制品并停止，不得降级使用全 T17 G0 权重后仍称严格 family 隔离。
