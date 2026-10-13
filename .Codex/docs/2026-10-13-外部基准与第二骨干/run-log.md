# run-log：P1 外部近邻与第二骨干复现（2026-10-13 启动）

> 实现代理：`实现-外部近邻与第二骨干`（模型 opus，effort high）。
> 冻结计划：本目录 `implementation_plan.md`。上游依据：`thesis/methods/第三章-基线与消融比较清单.md` §3.1–§3.2、§四。
> **本日志只记机械事实与缺口，不下候选存废裁决。**

## 阶段 0：前置核查（完成）

- **第二骨干 B 分支缺陷核查**：`bresnet_p2p3.py`（`IMPLEMENTATION_VERSION = bresnet_p2p3_b_fix_v1`）
  的 B 分支**已真实存在**（显式 `if arm == "B"` 路径：每恶意样本 1 个 `perturb2` 变体追加入批；
  `normalize_arms` 校验臂名）。清单 §1.3 记录的「B 落入 A 路径」历史缺陷此前已修复。
  本轮追加运行时断言：批内含恶意样本时 `adv_batch` 必非空，否则 `assert` 失败——B 不可能再静默退化为 A。
- **既有臂零扰动断言（通过）**：`verify_zero_disturbance.py` → `zero-disturbance-audit.json`。
  D/F/UQ/CAND4/EDIT4 五臂与断点保存收据**逐字段一致**；B 臂（2026-09-23 旧 schema checkpoint）
  无缓存收据字段（缓存收据机制 2026-10-13 才引入），降级为「重放确定性」断言（两次 rebuild 一致）+ 
  git diff 复核 rebuild 代码路径未改动。**该降级如实登记，不视为通过**——主代理可决定是否补齐 B 的收据可比性。
- 评价算子 `ch3_drift_formal_edit_v2.py` 哈希核验：`fb6f5429…` 不变 ✓。
- 训练器五臂实现提交于 3a786907 + load_split 修复 5ac814fb（sha256 `804dfe82…`）；
  bresnet EDIT4/UQ 于 20426243（sha256 `51ba661c…`）。

## 阶段 1：实现缺陷自报（2026-10-13 当轮）

1. **误删 load_split 签名**：插入 `hotflip_variants` 时把 `def load_split(...)` 行当锚点替换未补回，
   函数体变成不可达代码。`py_compile` 通过（不可达代码合法），由零扰动断言的真实运行暴露。
   已修复（5ac814fb）并验证导入可用。教训：插入函数时锚点行必须包含在 new_string 中。
2. **多次 Edit/Write 输出损坏**（约 8 处占位符/语法损坏，全部当场发现修复）：
   长文本编辑中出现 `占位`/`placeholder` 类伪代码混入。对策已固化为「编辑后立即 py_compile + rg 扫描占位符」。
3. **凭记忆 API 错误两处**（真实探针暴露）：`model.embedding_c.weight`（实为
   `TokenEmbedding.embedding.weight`）；`alpha_ids` 广播形状错误（37 vs 43 维）。均由探针实测修复。
4. **dry-run 既有边界**：`--dry-run N`（N<10001）时评价面无恶意样本会崩——**既有入口问题**，
   非本次改动引入，未修复（不在授权范围）。本轮 dry-run 用 10002。

## 阶段 2：dry-run 入口检查（完成，2026-10-13）

- 四新臂 `--dry-run 10002`（1 epoch）全部通过：C1R / CEQ / CBN / DRICHEL 均完成训练+评价里程碑。
- HotFlip 真实模型探针（8 个真实 T17 DGA 域名，预算 2）：平均 p_mal 下降 0.44，4/8 被骗到 p<0.5，
  攻击方向正确（最大化恶意类 CE）。
- **登记接口偏差**：HotFlip 贪心允许两步命中同一位置（净编辑 1 位，如 `google-vorify.org`），
  实际编辑位数 ≤ 名义预算 2——与 EDIT4/CURRICULUM 的「名义位数因位置碰撞饱和」同类现象，如实登记。
- 干跑制品在 /tmp/p2p3-dryrun-newarms（可丢弃）。

## 数值登记（待主代理确认；先按登记值执行）

| 数值 | 用途 | 依据 | 状态 |
| --- | --- | --- | --- |
| ρ=0.5（\|A\|=30000/60000） | ESAT 子集比例 | ESAT 笔记 L33：原文 CIFAR 中点配置 25000/50000=50% 的同比例映射；原文未给通用比例 | 待确认 |
| M=3 快照 | ESAT 跨快照熵平均 | A 臂 3 轮逐 epoch 快照；原文未给 M | 待确认 |
| 熵定义 −p·log p−(1−p)·log(1−p) | ESAT 评分量 | ESAT 笔记式(3)原文（自然对数） | 已核原文 |
| HotFlip 预算=2、ALPHA 37 字符、greedy | DRICHEL 攻击接口 | 实施计划「固定编辑预算内」「一阶近似」+ 与 perturb2 同界 | 计划冻结 |
| C1R 替换语义（前 ceil(m/2) 个恶意替换） | C1R 批组装 | 实施计划「以 1:1 比例被替换」（恶意侧内部 1:1 的唯一自洽读法） | 待确认 |
| C1R/CEQ 缓存键 | 缓存身份 | 沿用样本索引键 + cache_policy_id 含臂名 + 断点含轮次（与既有臂同构优先于字面「键含臂名轮次」） | 待确认 |
| CBN 权重 3.0 | 良性类权重 | 清单 §3.1「沿用组件 2 已登记系数」 | 计划冻结 |
| CEQ ce=−log(clip(p,1e-12,1)) | 排序量 | 数值防御；CE 与 p 单调等价不改变排序 | 任务化设定 |
| DRICHEL 入批 min(64,m) | 恶意侧暴露 | UQ 同构均匀流（种子 42+13）；池=m（每恶意 1 变体），与 UQ 的池 4m 不同，暴露如实单列 | 待确认 |

## 阶段 4：DRIFT 侧五臂逐臂读数（正式训练，diagnostic spec 全量 60000，3 轮 × batch 128 × seed 42）

### ESAT（完成，2026-10-14）

- 结果 JSON：`/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-source-common-esat-mps-20261013-v1/arm-ESAT-result.json`
  （SHA-256 `290cb1522330a0eb0d13913921cc6e733cefc3925814c351806487f249419497` 为同目录 arm-ESAT-checkpoint.pt）
- 筛选面板读数（历史 0.5 阈值，非正式低误报口径）：clean FPR `0.0336` / FNR `0.0211`；
  adv_k2 FNR `0.0218`；adv_krand FNR `0.0215`；adv_maskdga FNR `0.0184`（每面板 n=30000 恶意）。
- 墙钟 `3395.7s`（≈56.6 min；0.56 批/s，慢于 A 臂 0.72 批/s 的差量 = 子集过滤与变体生成）。
- 身份比对：code_sha256 `804dfe82…`（新训练器）、spec `5e46e4ce804a`（与既有八臂同一份）、
  esat_subset_sha256 已入 identity（绑定 3 快照哈希）；MPS 单进程约束全程满足。
- 正式 p0 读数待五臂齐后统一评价。

### C1R（完成，2026-10-14）

- 结果 JSON：`/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-source-common-c1r-mps-20261013-v1/arm-C1R-result.json`
  （arm-C1R-checkpoint.pt SHA-256 `db2fb8ec8df4b9dd40fe4873a7618eee45d804a1fa2ef9076c6fc2c2b0bc92ed`）
- 筛选面板读数：clean FPR `0.0224` / FNR `0.0327`；adv_k2 FNR `0.0320`；adv_krand `0.0313`；adv_maskdga `0.0268`。
- 墙钟 `2827.1s`（≈47.1 min；0.723 批/s，与 A 臂同速——替换语义无额外变体批量）。
- 身份比对：code_sha256 `804dfe82…`、spec `5e46e4ce804a`；变体缓存与 B 同核同流（rebuild 路径共用 B 分支）。
- 对照参照（既有 B 臂筛选面板，arm-B-result.json 实测：clean FPR `0.0333` / FNR `0.0215`；
  adv_k2 FNR `0.0213`；adv_krand `0.0211`；adv_maskdga `0.0161`；wall 16391.6s 历史并发条件读数）——
  C1R 的对抗暴露为 B 的一半（ceil(m/2)/批 vs m/批），其 maskdga FNR 高于 B（0.0268 vs 0.0161）
  与该暴露差方向一致；机械读数仅供主代理裁决，不在此下结论。
- **自报缺陷（2026-10-14）**：本日志初稿在此处写过一组未经核对的 B 臂「对照数字」
  （0.0222/0.0271/0.0182），属凭空生成读数，已用实测值替换。核实方式：直接读
  arm-B-result.json。教训与「汇报提到的数字必须实测」一致，已记入检查清单。

### CEQ（完成，2026-10-14）

- 结果 JSON：`/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-source-common-ceq-mps-20261013-v1/arm-CEQ-result.json`
  （arm-CEQ-checkpoint.pt SHA-256 `d9c84a34d5b8b88da8ee558b7570709ecba610a0f6b513845c70e7ac60b5b909`）
- 筛选面板读数：clean FPR `0.0455` / FNR `0.0177`；adv_k2 FNR `0.0148`；adv_krand `0.0140`；adv_maskdga `0.0085`。
- 墙钟 `4704.9s`（≈78.4 min；0.37 批/s，四候选池评分前向的开销，与 D/F 同一评分路径量级）。
- 身份比对：code_sha256 `804dfe82…`、spec `5e46e4ce804a`；候选池与 D/F 逐字同核
  （rebuild 走 D/F 同款 else 分支），唯一差量 = 未中心化 CE 排序。
- 机械观察（不下结论）：CEQ 的 clean FPR（0.0455）明显高于同面板 B（0.0333），与
  「全局 CE top-q 持续选入最难候选、牺牲干净边界」方向一致，正式裁决留主代理。

### CBN（完成，2026-10-14）

- 结果 JSON：`/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-source-common-cbn-mps-20261013-v1/arm-CBN-result.json`
  （arm-CBN-checkpoint.pt SHA-256 `ab37ce6878eea8748bd4b1e29c965d9721dad9903f0f8557878b95f4a97be547`）
- 筛选面板读数：clean FPR `0.0121` / FNR `0.0463`；adv_k2 FNR `0.3628`；adv_krand `0.3558`；adv_maskdga `0.6767`。
- 墙钟 `~2830s`（≈47 min；0.72 批/s，无对抗增广路径，与 A 臂同速）。
- 身份比对：code_sha256 `804dfe82…`、spec `5e46e4ce804a`；无对抗分支（走 A 路径）+ 损失分支
  全体真良性 CE×3.0（权重沿用组件 2 冻结系数）。
- 机械观察（不下结论）：固定权重把干净 FPR 从 A 的 0.0224 压到 0.0121，代价是三攻击面板
  FNR 大幅上升（maskdga 0.0182→0.6767）——静态类代价的机械后果，正式裁决留主代理。

- **ESAT 子集冻结（完成）**：`esat_selector.py` 消费 A 臂 3 快照（ep1/ep2/ep3），
  全源训练集 60000 样本跨快照平均熵（−p·log p−(1−p)·log(1−p)，自然对数）降序排序，
  ρ=0.5 → |A|=30000（恶意 14852 / 良性 15148；熵排序未强烈偏向恶意——A 臂模型对两类
  都高置信，属机制本身特性，如实登记）。子集清单：`…/ch3-drift-source-common-a-snapshot-mps-20261013-v1/esat-subset-rho0.5-v1.json`
  （绑定 3 快照哈希 + spec sha 5e46e4ce804a；子集写入 ESAT 运行目录曾被 main 的空目录
  检查拒绝，已移至选择器产物目录）。ESAT 对抗暴露 ≈ B 的 49.5%（14852/30000 恶意样本
  各 1 个变体）。

- A 臂快照重跑启动 2026-10-13（P2P3_OUT=ch3-drift-source-common-a-snapshot-mps-20261013-v1，
  `--arms A --selector-snapshot-dir …/selector-snapshots`；同刻 1 个 MPS 进程已断言）。
  目的：为 ESAT 提供独立非鲁棒参照模型的 3 个逐 epoch 快照。既有 A 臂（20260923）制品不动。
- **重跑身份一致性（已验证）**：重跑 A 的 epoch 1 指标与既有 A 臂 fpr_curve[0] **逐位一致**
  （clean_FPR 0.023566666666666666 / attack_FNR 0.30846666666666667 / attack_AP 1.0）；
  epoch 3 出现微小漂移（重跑 clean_FPR 0.022333 vs 既有 0.022400，差 2 样本；attack_FNR
  0.318433 vs 0.317967）——判定为 MPS 浮点非确定性跨轮累积（epoch 1 逐位一致证明代码路径
  相同，漂移非代码差量），如实登记。ESAT 快照身份以重跑制品自身哈希为准，子集清单绑定
  快照哈希自洽。
- 提交 dddaf74b 范围混叠自报：`p0_legal_attack_probe.py` 在会话开始时携带上一轮
  （UQ/CAND4/EDIT4 评价改造）的未提交改动，本轮追加 RUNS/哈希表/动态汇总时被一并提交，
  未按「改前快照」规则先行拆分。未重写历史；文件内容正确（py_compile + --help 通过），
  但该提交混含上一轮工作，请主代理知悉。
- 后续串行队列：A-snapshot → ESAT 子集计算 → ESAT → C1R → CEQ → CBN → DRICHEL → p0 评价五臂。
- 第二骨干队列：bresnet dry-run → A/B/EDIT4/UQ/D 五臂 → 读数交付。

## 待办与缺口

- p0 评价端 `p0_legal_attack_probe.py` 需追加 5 臂到 RUNS / EXPECTED_CODE_SHA256，并把
  `gate_mechanical` 汇总分支对缺臂动态化（陷阱 4）。评价前完成。
- 第二骨干五臂的读数口径 = bresnet 内置四面板（T18 val 7500/类 + k2/krand/maskdga），
  与 DRIFT 侧 p0 正式口径（30000 源验证、0.1% 预算）**不同层**，交付时如实标注。
- B 臂缓存收据缺口（阶段 0）待主代理裁决是否接受降级断言。
