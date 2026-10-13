# Uniform-q（UQ）对照臂运行日志（2026-10-13）

> 生命周期：本任务期间的过程记录与检查点；终局读数交主代理裁决，正文/台账不据本文件作结论。
> 派发记录见同目录 `dispatch-log.md` 的 D-3 条。

## 一、目的与隔离结构（预先冻结）

源期 B／D／F 三臂存在**双因素混杂**：B 的候选核是「原串一次二位编辑」，D／F 的核是
「共享 base 上的两阶段复合四候选核」（累积 4 位）；两者同时在**候选核**与**选择规则**上不同，
故 B vs D／F 不能单独归因于组中心化选择规则。UQ 臂只改选择规则。

**UQ 定义**：候选核与 D／F 逐行相同（`adv_cache[i] = [perturb2(perturb2(orig), ...) × 4]`），
唯一差量 = 入损失的 64 个变体由「组内中心化优势（fooled − 组均值）跨组 top-64 竞争」
换为「同一候选池上均匀随机取同配额 64」。选择使用独立 `random.Random(SEED+13)` 流，
不消耗攻击 RNG，故候选池与 D 逐条相同。损失为 plain CE（无良性误报加权）。

**诚实标注的三处对照口径差异**（不因任务简报措辞而放宽）：

| 对照 | 严格隔离的因素 | 备注 |
| --- | --- | --- |
| **UQ vs D** | **纯选择规则** | 同核、同配额、同 plain CE；唯一差量确实只有选择规则 |
| UQ vs F | 选择规则 **＋** 良性误报加权（×3.0） | F 另含良性补偿 ⇒ **非**纯选择规则对照 |
| UQ vs B | 候选核 **＋** 装配规则 | B 为原串一次二位编辑且每恶意样本仅 1 变体全量入批（≈M≈64），UQ 为 4 候选池均匀取 64 ⇒ 非纯候选核对照 |

## 二、文件改动与身份

| 项 | 值 |
| --- | --- |
| 训练脚本（改动前，即 D／F 代码版本）SHA-256 | `0705c24be7e5cbc0716a99f360781bb9394378d34e2ed96103077961d4bbacef` |
| 训练脚本（改动后，含 UQ 分支）SHA-256 | `59d50aaf71d19b9ff796b1785b5f053d0b1bf68da49e6f226201d0666903155b` |
| 评分脚本（新建） | `.Codex/docs/2026-09-23-DRIFT源期训练抽样合同/uniformq_low_fpr_probe.py`，SHA-256 `a0984d924f1bfea7b16eace11ba8486773ad74a63494d27f7b7b8496bdd0999c` |
| 训练运行目录（评分） | `thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-source-lowfpr-bdfu-mps-20261013-v1/`（输出 `source-low-fpr-probe.json`） |
| UQ 断点 SHA-256（权重身份） | `63a168864bba57ff61bfd5a570cb5b6ca4a9f28e628763a00fe2e7111e76f2e8`（与 A `99f8c3a2`／B `2f3e1a26`／D `bfaed8f1`／F `15317a8c`／G `129c3c8e` 互异） |
| 训练运行目录 | `thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-source-common-uniformq-mps-20261013-v1/` |
| 结果文件名 | `source-common-uq-result.json`（臂键 `UQ`，展示名「均匀同配额选择（同 D/F 候选核，隔离选择规则）」） |

**Git 状态说明**：`official_p2p3.py` 在工作树中**已有他人（D-1）未提交改动**（即上面 `0705c24b…`
的无明文断点修订）。按仓库「不得暂存其他代理既有改动」与任务「不要 commit」，
本次只在同文件追加 UQ 分支，**未 commit、未 stash、未回滚**。

改动清单（全部为新增 UQ 分支，不动既有臂语义）：

- `ARM_DISPLAY_NAMES["UQ"]`、`CACHE_POLICY_BY_ARM["UQ"]`、`rebuild_first_epoch_cache` 接受 `UQ`；
- `uniform_rng` 独立流 + 断点保存/恢复（UQ 恢复时强制校验其存在）；
- 分支头 `elif arm in ("D","E","F","H","UQ")`，选择尾改为 `if arm == "UQ": 均匀取 64 else: scored[:64]`；
- `main()` 臂白名单报错文案；模块 docstring 与常量注释说明差量。

## 三、身份收据对照（训练侧，逐项）

（下表由运行目录 `run-status.json` 的 `identity` 段与任务表逐项比对；✅＝一致）

| 字段 | 任务表要求 | UQ 实际 |
| --- | --- | --- |
| member_selector_sha256 | 6dabfa81… | ✅ 6dabfa8152ef43beecd766398c08af87b354673eaa79d1c4adca0c75cfd3b510 |
| model_loader_sha256 | 47a5fe57… | ✅ 47a5fe57ba303d51bee7777e21a7ce5bf5b64340a05e78a679f06fa22a204dd1 |
| feature_adapter_sha256 | 6a6902cf… | ✅ 6a6902cfe800a3b33189a706a0667bb88933bcde03e76081d8ad2256d20e0df8 |
| candidate_spec_sha256 | 5e46e4ce… | ✅ 5e46e4ce804a2b4eff5d910513f02642e0aa651a3ff04152d3fe1fce9139cea7 |
| checkpoint_sha256 | 090e5f84… | ✅ 090e5f844492ee532f72f8b1db1cb335bf67c9468fd2e0329344fe209b5969c3 |
| source_revision | drift-dga-2026-rev-… | ✅ drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521 |
| epochs / batch / seed / precision | 3 / 128 / 42 / fp32 | ✅ 3 / 128 / 42 / fp32（device=mps） |
| **唯一差异** | 选择规则 | ✅ `code_sha256`（`59d50aaf…` vs D/F `0705c24b…`）与 `arms=["UQ"]` |

## 四、执行记录

- 11:29 CST 建立洁净运行目录（仅 `console.log`），`py_compile` 与 `--help` 通过。
- 11:29 CST 以 `nohup … disown` 独占启动（无并发 MPS 任务）；`--arms UQ --result-name source-common-uq-result.json
  --candidate-spec .Codex/docs/2026-09-23-DRIFT源期训练抽样合同/candidate-spec-diagnostic-v1.json`。
- 源成员选择按角色正常推进（12 个源训练角色 + 6 个源验证角色），身份段当场逐项对齐上表。
- 11:35:40 首个训练心跳（epoch 1/3 batch 1，loss `0.8919527`）；11:35→13:23 三轮训练 + 逐轮验证，
  每轮末原子写 `arm-UQ-checkpoint.pt`；13:30:48 整臂 `completed`（`wall_seconds=6701.8`，
  含源加载与逐轮评价；本机无并发 MPS 任务）。逐轮里程碑：
  epoch 1 干净 FPR `0.0303` / k2 FNR `0.0269`（2696.6 s）、epoch 2 `0.0301` / `0.0250`（2242.4 s）、
  epoch 3 `0.0314` / `0.0228`（1536.6 s）。
- 注意：`loss` 阶梯 B `0.44` < **UQ `0.89`** < D/F `~1.75`（batch 1）。UQ 与 D 的逐行路径相同而只换选择，
  故该差与「D 选最难（fooled）变体 ⇒ 初始 CE 更高」的机制预期一致，不是实现差异。
- 13:33–13:48 以 `uniformq_low_fpr_probe.py` 完成 B/D/F/UQ 四臂源验证低误报复评，
  输出 `ch3-drift-source-lowfpr-bdfu-mps-20261013-v1/source-low-fpr-probe.json`（`status=completed`）。

## 四之二、结果（`screening_only`；不作晋级/淘汰裁决）

**硬门全部通过**：四臂身份 12 项公共字段一致；原 0.5 干净 FP/FN 对各自 `arm-*-result.json` **全数复算一致**
（B `999/645`、D `1200/588`、F `859/920`、UQ `942/745`）；B/D/F 两档 DGA FN 与阈值**逐位等于 v3 已发布值**
（`v3_reproduction_all_dga_fn_equal=true`，阈值小数点后 10 位相同），成员收据 `3d4e9b0e…c0e05` 与 v3 一致。

**候选池同核（UQ vs D）**：`identical=true`，UQ 重放池在 D 策略标识下的根
`7d543243b91dc6b27a47606f723dba468984ce346c0aa10e527dc359d84b366c` 与 D 断点记录**完全相同**；
两臂池对象级相等（30,000 组 / 120,000 候选），`source_order_sha256` 一致。

| 臂（源验证 30,000 良性 + 30,000 DGA 同成员） | 0.5 干净 FP / 干净 DGA FN | k2 / krand / mask FNR@0.5 | 0.1%（30/30,000）DGA FNR | 1%（300/30,000）DGA FNR |
| --- | ---: | ---: | ---: | ---: |
| B 朴素增广 | 999 / 645 | 0.0213 / 0.0161 / 0.0161 | **24.857%**（7,457） | **6.477%**（1,943） |
| D 组中心选择 | 1,200 / 588 | 0.0173 / 0.0105 / 0.0105 | 26.260%（7,878） | 7.163%（2,149） |
| F 选择＋补偿 | 859 / 920 | 0.0246 / 0.0165 / 0.0165 | 25.677%（7,703） | 7.113%（2,134） |
| **UQ 均匀同配额** | **942 / 745** | 0.0228 / 0.0161 / **0.0161** | 26.820%（8,046） | 6.880%（2,064） |

**配对净差（`net(right−left)`，正=left 多漏检）**：
- 0.1%：UQ vs B `-589`（−1.963 pp，UQ 更差）、UQ vs D `-168`（−0.560 pp，UQ 更差）、UQ vs F `-343`（−1.143 pp，UQ 更差）；
- 1%：UQ vs B `-121`（−0.403 pp，UQ 更差）、UQ vs D `+85`（+0.283 pp，**UQ 更好**）、UQ vs F `+70`（+0.233 pp，**UQ 更好**）。
- 复算既有对照与 v3 一致：0.1% B−D `+421`、B−F `+246`；1% B−D `+206`、B−F `+191`。

**隔离出的两个差量方向（只报方向，不裁决）**：
1. **选择规则（UQ vs D，唯一差量）**：改均匀同配额后，0.5 干净 FPR 由 `0.0400` 降至 `0.0314`（−0.86 pp），
   但干净 DGA FNR `0.0196→0.0248`（+0.52 pp）、k2 `0.0173→0.0228`、mask `0.0105→0.0161` 均升高；
   源冻结两档方向相反：0.1% 更差 0.560 pp、1% 更好 0.283 pp。⇒ 组中心跨组竞争的独立贡献是
   **以干净误报换取干净 DGA 与攻击检出**；在低误报源冻结工作点上方向随预算翻转且量级 ≤0.6 pp。
2. **候选核＋装配（UQ vs B）**：UQ 在 0.5 干净 FPR 略低（0.0314 vs 0.0333），但干净 DGA FN 更高
   （745 vs 645），mask 面板**完全相同（482/30,000）**，低误报两档**均更差**（0.1% 差 1.963 pp、1% 差 0.403 pp）。
   ⇒ B 相对 D/F 的干净优势**不能**由选择规则解释；把核换成 D/F 的两阶段四候选核并只保留均匀同配额选择，
   干净 DGA 检出反而更差。**注意**该对照同时含装配规则差异（B 每恶意样本 1 变体全量入批），
   故只能称「核＋装配」，不能称纯候选核。

**结论边界**：单训练种子、源训练/验证有 326 个唯一域名重合、`screening_only` 固定 0.5 与源冻结干净面板；
未生成攻击 v2、未读 T20–T25。G 臂无同口径低误报读数，未纳入本表。


## 五、同核（候选池同一性）核验方法

训练完成后，用 `official_p2p3.rebuild_first_epoch_cache("UQ", train_d, train_y, 3)` 重放首轮池，
再以 **D 的策略标识** `source_screen_d_base4_if_missing_v1` 调 `cache_summary(...)`，
与 **D 断点记录的 `cache_root_sha256`**（`7d543243b91dc6b27a47606f723dba468984ce346c0aa10e527dc359d84b366c`）
比较：相同 ⇒ 两臂候选池逐条相同（同一核）；不一致即按阻塞条件停止。
评分脚本已把该核验做成硬门（`uq_candidate_pool_identity_vs_D.identical`）。
