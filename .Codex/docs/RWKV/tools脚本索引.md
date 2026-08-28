# tools/ 脚本索引（第三、四章）

- **状态日期**：2026-08-28。
- **范围**：`thesis/experiments/llm_probe/tools/` 目录**顶层** `.py` 文件，共 **122 个**（任务简报给出的
  预期数为 121，实际盘点多 1 个；差额是另两个实现代理在本次索引编制期间新建的
  `ch3_ft_entity_memory_interface.py` / `ch3_ft_causal_entity_memory.py` / `ch3_ft_entity_stratified_sampler.py`
  三个文件——简报已预告这三个文件"可能在工作期间才出现"，本索引按盘点时的真实状态照录，不删减、不等待）。
  子目录（`env/`、`remote_exec/`、`lspr24_g0/`、`dijk2026_replication/`、`_resume_audit/`、
  `ch3_final_weights_assets/`、`r2_genis_totbytes_verifier/`、`r2_quic_qlog_audit/`）不在本次盘点范围内；
  `remote_exec/` 下是三个 `.exp`（expect）脚本，不是 Python，仅在此说明其为远程执行基础设施，不列入下表。

## 一、用途与免责声明

本索引**只读盘点**，不移动、不改名、不修改、不删除任何脚本文件。这些脚本的 `sha256`
被写进运行收据（`run-config.json`／`aggregate-results.json` 等制品）与科学身份哈希，
任何字节级改动都会使既有制品失去可追溯性、破坏已封印实验的复现校验。本索引的编制过程
只使用 `rg`／`fd`／`head` 等只读命令读取文件，未执行任何脚本、未连接服务器、未启动任何实验。

「用途」列一律摘自脚本模块级 docstring 的**第一句**，不做改写或臆测；无模块 docstring 的脚本
如实标注「无模块 docstring」，并在可行时用模块顶层常量或函数名做客观补充说明（不算作 docstring 摘录）。

「判据」列的证据优先级：
1. 任务简报给出的**已知状态锚点**（第三章活跃 FT 线清单）；
2. `RWKV第三章恢复卡.md` / `RWKV第四章恢复卡.md`（下称【恢复卡3】【恢复卡4】）；
3. `2026-08-28-全局进度快照.md`（下称【快照0828】）；
4. `2026-08-26-第三章跨骨干机制实验负结果档案.md`（下称【负档0826】）；
5. 脚本 docstring 之间的明确"取代/复制/派生"关系（下称【脚本互证】）——这类证据不是四份
   主控文档的直接点名，但来自脚本自身文档中可核查的文字（如"本文件由 X 复制后……"），
   本索引照实标注来源类型，不冒充主控文档命中。

以上均无法定位时，一律标「未确认」，不得臆断，见第四节清单。

## 二、总表（按状态分节）

### 2.1 活跃（35 个，当前主线在用）

| 脚本名 | 章节 | 路线 | 用途 | 判据 |
| --- | --- | --- | --- | --- |
| `ch3_ft_c00_dual_selection.py` | 第三章 | RWKV-FT | 裸 FT C00 的跨设备双选轮训练与真实运行校准 | 【已知锚点】任务简报直列 |
| `ch3_ft_transformer_field_token_protocol_a.py` | 第三章 | RWKV-FT | FT-Transformer 逐字段 Token 协议 A 四格实验工具（任务 1 至 5） | 【已知锚点】；【快照0828】"FT-Transformer 正式四格：C00 0.7508（全项目最高）" |
| `ch3_ft_causal_entity_memory.py` | 第三章 | RWKV-FT | 机制一（因果实体记忆交叉注意力）：记忆状态容器与交叉注意力模块 | 【已知锚点】（简报预告"可能在工作期间才出现"，盘点时已存在） |
| `ch3_ft_entity_memory_interface.py` | 第三章 | RWKV-FT | 机制一（因果实体记忆交叉注意力）严格过去接口构建器 | 同上 |
| `ch3_ft_entity_stratified_sampler.py` | 第三章 | RWKV-FT | 机制二：实体分层采样器（spec 5.4 节「每步按实体均匀抽正实体与负实体」） | 同上 |
| `ch3_lspr23_field_cardinality_receipt.py` | 第三章 | RWKV-FT | 生成 LSPR23 Protocol A 训练区七个字段的只读基数收据 | 【已知锚点】 |
| `ch3_lspr23_entity_history_availability.py` | 第三章 | RWKV-FT | 第三章 LSPR23 实体历史可用性诊断：为因果实体记忆机制提供动机与作用面证据 | 【已知锚点】 |
| `ch3_gradient_controller_conflict_probe.py` | 第三章 | RWKV-FT | 机制二梯度控制器冲突实测：在已收敛模型上量 ‖g_f‖ 与 ‖g_r‖ | 【已知锚点】 |
| `ch3_strong_backbone_scorelayer_backfill.py` | 第三章 | RWKV-FT | 把分数层 CPA-ELP 四格移植到 FT-Transformer 与 TabM32 的冻结 C00 逐流分数上 | 【负档0826】FT 分数层移植方向正但噪声级；【快照0828】"服务器待办 2. TabM32 分数层回填（工具已部署服务器，`39d918a`）"——同一工具的 TabM32 分支待续跑，仍在使用 |
| `ch3_backbone_protocolB_2x2_rerun.py` | 第三章 | 神经骨干消融 | 第三章基座消融协议 B：全注意力（transformer）与门控循环（gru）重跑 | 【快照0828】"服务器待办 1. 协议 B 目标年评价续跑（8 训练格已完成在数据盘；两条命令分钟级）→ U6 全注意力/GRU 定案" |
| `ch3_baselines_full_merge.py` | 第三章 | 基线对照 | 第三章基线重跑的合并与主比较表生成 | 【脚本互证】读取 `ch3_baselines_full_trees.py`/`ch3_baselines_full_neural.py` 结果生成正文主表，为当前正文比较表来源 |
| `ch3_baselines_full_neural.py` | 第三章 | 基线对照 | 第三章已发表基线重跑（神经模型族）：GRU + 全注意力 Transformer + 一维 CNN，全量冻结缓存 | 同上，正文外部基线来源 |
| `ch3_baselines_full_trees.py` | 第三章 | 基线对照 | 第三章已发表基线重跑（树模型族）：随机森林 + XGBoost，全量冻结缓存 | 同上 |
| `ch3_baselines_param_matched.py` | 第三章 | 基线对照 | 第三章已发表基线的等参数预算重跑：GRU + 全注意力 Transformer + 一维 CNN | docstring 自述"两版都进结果表，谁赢报谁"，与 full_neural 并列为正文对照来源 |
| `ch3_final_weights_freeze.py` | 第三章 | RWKV-FT/MLP | 第三章定稿模型权重固化（协议 A 四格重跑 + 逐位复现校验 + 归档打包） | 【负档0826】/【恢复卡3】第三节"正式 CPA×ELP 四格"为定稿证据链一环 |
| `ch3_full_mlp_complete_entity_lp_protocol_a_q0.py` | 第三章 | RWKV-MLP | 全容量 MLP 完整实体幂平均协议 A Q0 | 【恢复卡3】"位语义已源码核验：`tools/ch3_full_mlp_complete_entity_lp_protocol_a_q0.py:36-41`" |
| `ch3_full_mlp_complete_entity_lp_protocol_a_q0_bf16.py` | 第三章 | RWKV-MLP | 全容量多层感知机统一 BF16 协议 A 资格实验 | 【恢复卡3】"正式 CPA×ELP 四格（bf16，正文主消融源）"；【快照0828】"主消融=MLP bf16 四格 36.46/46.41/44.75/58.55" |
| `ch3_hparam_fairsel_v2.py` | 第三章 | 超参协议 | 第三章 CPA-ELP：统一「top-5 预测平均」检查点策略下的 24 配置超参搜索 + 2x2 四格重跑 | 【脚本互证】`ch3_baselines_full_merge.py` docstring 引用其 `selection_frozen.json` 作为"本章方法数字"来源，为当前生效协议 |
| `ch3_published_neural_operational_backfill.py` | 第三章 | 基线对照 | 用已持久化分数回填三种已发表神经基线的目标年运营指标 | 【脚本互证】服务于 `ch3_baselines_full_neural.py` 产出的正文运营指标表 |
| `ch3_xgb_cpa_elp_entity_oof.py` | 第三章 | 机制移植/XGBoost | 第三章 XGBoost 适配 CPA 与 ELP：源年实体折外选择和目标年四格评价 | 【负档0826】第二节"进正文的跨基座证据：XGBoost 分数层四格（机制移植）" |
| `ch3_xgb_cpa_elp_operational_backfill.py` | 第三章 | 机制移植/XGBoost | 为冻结 XGBoost＋CPA-ELP C11 回填完整目标年运营指标 | 同上，正文机制移植增益数据来源 |
| `ch3_xgb_entity.py` | 第三章 | 基线对照/XGBoost | XGBoost 基线的实体级评价，与冻结 C11 逐字对齐 | 【负档0826】第二节 XGB 分数层四格 `0.5132/0.5353/0.5304/0.5651` 的 C00 无机制基线来源 |
| `ch4_e1_source_entity_oof_gate.py` | 第四章 | RWKV-其他骨干/MLP | 第四章 E1 源年实体三折折外信号快速门禁 | 【恢复卡4】第二节"E1 源年实体折外信号门禁"完整机械状态记录 |
| `ch4_entity_length_bucket_diagnostic.py` | 第四章 | RWKV-其他骨干/MLP | 重跑第三章四格并诊断第四章实体流数分桶 | 【恢复卡4】第三节 3.1"感知机分桶"五桶实体 AP 增量数据来源 |
| `ch4_mlp_o11_crossyear_threshold_transfer_diag.py` | 第四章 | RWKV-MLP(O11) | 第四章跨年阈值迁移诊断：MLP O11 底座源年校准阈值搬到 LSPR24 的失配幅度存在性诊断 | 【快照0828】"三病灶全部实验确认……跨年失配（预算利用 22.2%、DR −16.62 点，`983ff49`）" |
| `ch4_mlp_o11_oof_fold_models.py` | 第四章 | RWKV-MLP(O11) | 第四章 D0：全容量 MLP O11 配置的源年三折折外评分模型物化（服务器正式版） | 【恢复卡4】5.1 节起全部 XGB/MLP 折外链的对应正式工具；【快照0828】"底座已按 V2 迁移至第三章胜出 MLP O11" |
| `ch4_mlp_o11_oof_fold_models_local_screen.py` | 第四章 | RWKV-MLP(O11) | 第四章 D0 本机筛选支线：全容量 MLP O11 三折折外模型（screening_only） | 【恢复卡4】5.3 节"当前服务器无 GPU，训练保持未启动"——服务器无 GPU 期间本机筛选是当前实际在用路径，供 D1/D2/S_a/M1′ 消费 |
| `ch4_mlp_o11_pathology_diagnostics_local_screen.py` | 第四章 | RWKV-MLP(O11) | 第四章 D1/D2 本机筛选：MLP 底座曝光病灶与长度桶条件风险再确认 | 【快照0828】"三病灶全部实验确认（校准 bug 修复重跑后，`recal-v1` 家族）" |
| `ch4_mlp_o11_stratified_tong_2x2_local_screen.py` | 第四章 | RWKV-MLP(O11) | 第四章 S_a/S_b 本机筛选：MLP 底座长度分层 Tong 证书 2×2 消融（screening_only） | 【快照0828】"机制 2：三构造原门否决……构造 C（前向逐层预算）贴边校准顶破证书①②③④败" 为本工具 `--construction` 分支产出 |
| `ch4_mlp_o11_tong_pooled_q0_local_screen.py` | 第四章 | RWKV-MLP(O11) | 第四章 M1′ 本机筛选：MLP 底座池化 Tong 路径最大证书（screening_only） | 【快照0828】"机制 1（Tong 路径预算控制）：SUPPORTED（本机筛选级）……M1′ `0.0370/0.8954`" |
| `ch4_xgb_entity_exposure_lesion_source_diagnostic.py` | 第四章 | XGBoost | 零训练诊断实体重复曝光是否同时造成误报突破与迟到正检出 | 【恢复卡4】5.2 节"机制一重复曝光联合病灶……`MECHANISM1_PATHOLOGY_QUALIFIED`" |
| `ch4_xgb_entity_path_max_np_q0.py` | 第四章 | XGBoost | 用源年折外实体路径最大统计量执行零训练 Q0 | 【恢复卡4】5.3 节"`MECHANISM1_PATH_MAX_TONG_Q0_QUALIFIED`" |
| `ch4_xgb_long_entity_bucket_diagnostic.py` | 第四章 | XGBoost | 零重训诊断 XGBoost 在 LSPR24 长实体上的四格收益方向 | 【恢复卡4】第三节 3.2"XGBoost 分桶"五桶实体 AP 增量数据来源 |
| `ch4_xgb_path_max_tong_final_model_source_seed42.py` | 第四章 | XGBoost | 训练种子 42 最终单模型并执行源年实体路径最大 Tong 六臂评价 | 【恢复卡4】5.3 节"`-rerun2` 为 `finished/complete/exit=0`……结果数字待验收；不得再写「实现仍在进行」" |
| `ch4_xgb_path_risk_length_bucket_source_diagnostic.py` | 第四章 | XGBoost | 按冻结长度桶诊断源年实体路径最大风险，不训练新模型 | 【恢复卡4】5.4 节"池化 FPR 掩盖长度条件风险，病灶获单种子诊断支持" |

### 2.2 基础设施（35 个，数据/评价/表格/远程/校验类通用工具）

| 脚本名 | 章节 | 路线 | 用途 | 判据 |
| --- | --- | --- | --- | --- |
| `build_ch3_xgb_parent_recovery_proof.py` | 第三章 | 基础设施 | 为中断的第三章 XGBoost 父运行生成独立恢复证明 | 功能为运行恢复证明工具，非科研候选，四份主控文档未单独提及 |
| `ch3_alert_budget_curves.py` | 第三章 | 基础设施 | 告警预算曲线重分析：对已落盘的 LSPR24 逐流分数重新计算实体级检出率随假阳率的曲线等 | 【已知锚点】任务简报直列为基础设施 |
| `ch3_backbone_gru_precision_probe.py` | 第三章 | 基础设施 | 只读诊断：判定「打包批前向 vs 逐条截断前向」的 2.4e-4 差异来自 TF32 精度还是掩码错误 | docstring 自述"不训练、不评价、不写盘、不创建运行身份"，为骨干实现正确性核验工具 |
| `ch3_backbone_models.py` | 第三章 | 基础设施 | 第三章基座骨干共享定义：从 `ch3_backbone_protocolA_v2.py` 抽取，供协议 A/B 等多个入口 import 复用 | docstring 自述"纯定义模块……供协议 A/B 等多个入口 import 复用"，被 `ch3_backbone_2x2_local_screen.py` 等消费 |
| `ch3_backbone_read_mlp_ref.py` | 第三章 | 基础设施 | 只读：打印 ch3-hparam-fairsel-v2（top-5 预测平均协议）的 2x2 四格 LSPR24 指标 | docstring 自述"用于跨基座对照表的骨干 A（MLP）参照列。不训练、不评价、不写盘" |
| `ch3_build_metrics_table.py` | 第三章 | 基础设施 | 从第三章原始运行制品机械生成统一指标总表 | 【已知锚点】任务简报直列 |
| `ch3_common_first_alert_fp_budget_envelope.py` | 第三章 | 基础设施 | 五个既有系统在 LSPR24 上的共同实际首次告警 FP 预算包络 | 【已知锚点】；【恢复卡3】"N-16 共同 FP 预算包络……只是零训练评价修复，不是机制证据" |
| `ch3_crossL_fair_val.py` | 第三章 | 基础设施 | 诊断跨 L 排序是不是验证集口径漂移的产物 | docstring 自述"不改变主运行已冻结的胜者……不创建 SwanLab 运行身份"，为协议正确性核验工具 |
| `ch3_cuda_rwkv_raw83_qualification.py` | 第三章 | RWKV 训练路径 | 独立 CUDA-RWKV Raw83 资格单入口 | 【恢复卡3】第五节"独立 CUDA-RWKV 正式源年训练"；`.Codex/docs/RWKV/AGENTS.md`"RWKV 唯一活动训练路径是独立 CUDA 融合实现"——本工具是该路径的资格门禁基础设施 |
| `ch3_fairsel_apicheck.py` | 第三章 | 基础设施 | `ch3_2x2_fairsel.py` 用到的、相对 `ch3_full.py` 新增的 PyTorch 接口的运行时核验 | docstring 自述"只做接口存在性与语义核验……不产生任何科学结论、不注册运行身份" |
| `ch3_fairsel_xgb_matched.py` | 第三章 | 基础设施 | 把 XGBoost 基线的 Lp 聚合口径对齐到新协议 C11 学到的 p，做同 p 比较 | docstring 自述"只读 CPU 作业……不训练、不创建运行身份"，为口径对齐分析支持工具 |
| `ch3_full.py` | 第三章 | 基础设施（冻结参照实现） | 第三章双机制 2x2 交互实验（对齐 Dijk 2026 §5.9 训练协议） | 被 `ch3_2x2_fairsel.py`/`ch3_attribution.py`/`ch3_xgb_entity.py` 等十余个工具以"逐字复刻 `ch3_full.py` 第 X-Y 行"方式引用为代码口径基准，仍是当前活跃代码规范源 |
| `ch3_full_capacity_mlp_source_screen.py` | 第三章 | 基础设施 | 第三章全容量多层感知机的 LSPR23 C00 容量与配方筛选入口 | 【脚本互证】为全容量 MLP（O11 前身）容量/配方筛选前置工具，其产物是当前正文主消融模型的选型基础 |
| `ch3_grande_swanlab_publish_repair.py` | 第三章 | 基础设施 | 只读绑定 GRANDE 已完成制品并修复 SwanLab 聚合指标发布 | docstring 自述为工程发布修复工具，不涉及科研判据本身 |
| `ch3_hparam_probe.py` | 第三章 | 基础设施 | 超参搜索的规模探针：只读 LSPR23 侧，估算各 L 的序列数、切分规模与步数预算 | docstring 自述"不训练、不评价、不创建运行身份、不触碰 LSPR24"，为 hparam_fairsel 系列启动前的规模估算工具 |
| `ch3_neural_backbone_source_oof_gate.py` | 第三章 | 基础设施 | 第三章神经骨干源年实体三折折外资格门 | 与 `ch3_rwkv7_cpa_elp_source_oof_gate.py`/`ch3_tabm_cpa_elp_source_oof_gate.py` 同族，为跨骨干通用资格检查工具 |
| `ch3_p1_strata.py` | 第三章 | 基础设施 | P1 第 1 步：在 LSPR23 实体不相交验证集上统计实体流数分布，确认难分层是否可用 | docstring 自述"纯 CPU，不训练、不推理、不创建 SwanLab 运行身份"，为分层可行性探针，四份主控文档未记录后续 P1 第 2 步或采用结论 |
| `ch3_protocol_a_raw83_prepare.py` | 第三章 | 基础设施 | Protocol A Raw83 共享预处理 P0–P5 幂等阶段入口 | 被 `ch3_tabular_resnet_paper_recipe_protocol_a.py`/`ch3_tabm32_paper_recipe_protocol_a.py` 等多个协议 A 生产工具依赖的共享预处理入口 |
| `ch3_rwkv7_cpa_elp_source_oof_gate.py` | 第三章 | RWKV 训练路径 | 第三章 RWKV-7 与 CPA/ELP 源年实体三折折外资格门 | 与 `ch3_neural_backbone_source_oof_gate.py` 同族基础设施，服务于 RWKV-7 骨干资格核验 |
| `ch3_rwkv7_k0_fused_benchmark.py` | 第三章 | RWKV 训练路径 | RWKV-7 K0 纯 PyTorch 与 CUDA 融合核等价性和速度基准 | 为独立 CUDA 融合实现的等价性/速度基准核验工具，`.Codex/docs/RWKV/AGENTS.md` 要求"CUDA 入口不可用、编译失败或结果不合格时，记录精确工程或科学失败" |
| `ch3_rwkv_cuda_self_gate.py` | 第三章 | RWKV 训练路径 | CUDA-RWKV 小型容量自身资格门 | docstring"只有显式执行 `--run` 才会加载官方 CUDA 核并运行固定构造输入资格检查"，为独立 CUDA 融合路径训练前置门禁 |
| `ch3_sortkey_audit.py` | 第三章 | 基础设施 | 序列排序键只读核实：判定 dijk-repro 缓存里的 I23/I24/T23 用的是哪个时间字段 | docstring 自述"只读，不写任何缓存，不占 GPU"，四部曲之一，为因果排序正确性核验工具 |
| `ch3_sortkey_audit2.py` | 第三章 | 基础设施 | 序列排序键核实第二部分：量化按起始时间排序带来的因果性偏差 | 同上四部曲之二 |
| `ch3_sortkey_audit3.py` | 第三章 | 基础设施 | 序列排序键核实第三部分：按位置统计前缀里的"未来完成流" | 同上四部曲之三 |
| `ch3_sortkey_audit4.py` | 第三章 | 基础设施 | 序列排序键核实第四部分：把同一组判据补到训练年度 LSPR23 | 同上四部曲之四 |
| `ch3_tabm_cpa_elp_source_oof_gate.py` | 第三章 | 基础设施 | 第三章 TabM 式骨干源年实体三折折外资格门 | 与 `ch3_neural_backbone_source_oof_gate.py` 同族资格门基础设施 |
| `ch3_trunc_probe.py` | 第三章 | 基础设施 | P2 可行性探针：1e-7 截断是否真的压住了实体 AP | docstring 自述"纯 CPU，不训练、不改机制、不创建 SwanLab 运行身份"，为探针工具 |
| `ch3_valset_crossL_audit.py` | 第三章 | 基础设施 | 只读诊断：24 配置跨 L 排序时，LSPR23 验证集的逐流集合在 L=32/64/128 下是否相同 | docstring 自述"只读……不训练，不建运行身份" |
| `ch3_xgb_cpa_elp_eval_continuation.py` | 第三章 | 基础设施 | 从已冻结的源年模型接续 XGBoost+CPA+ELP 的 LSPR24 评价 | docstring 自述"不训练、不中间保存逐样本分数"，为评价接续支持工具 |
| `cuda_rwkv_official_backend.py` | 共用 | RWKV 训练路径 | 独立 CUDA-RWKV 官方融合后端 | `.Codex/docs/RWKV/AGENTS.md`"RWKV 唯一活动训练路径是独立 CUDA 融合实现……不得复用任何历史训练实现"——本文件是该路径的核心后端 |
| `neural_precision_runtime.py` | 共用 | 基础设施 | 单卡神经训练精度、等效微批量与资源收据共享脚手架 | 被 `ch3_tabm32_paper_recipe_protocol_a.py`/`ch3_ft_transformer_field_token_protocol_a.py` 等当前活跃工具依赖的精度合同脚手架 |
| `rwkv7_k0_fused_backend.py` | 共用 | RWKV 训练路径 | RWKV-7 K0 基础 WKV CUDA 融合后端 | 支撑独立 CUDA 融合路径的基础核后端，被 `ch3_rwkv7_k0_fused_benchmark.py` 消费 |
| `select_signal.py` | 共用 | 基础设施 | docstring 为 `ch3_full.py` 残留头（未更新）；实际功能是验证集切分逻辑来源 | 被 `ch3_2x2_fairsel.py`/`ch3_p1_strata.py`/`ch3_backbone_2x2_local_screen.py` 等多个工具明确"逐字照抄 `tools/select_signal.py` 第 151-168 行"引用，是当前仍在被引用的切分代码源 |
| `selftest_ch4.py` | 第四章 | 基础设施 | 三条路径的逻辑自检：在已知真值的合成数据上验证公式实现是否正确 | docstring 明确为公式实现自检工具，非科研候选 |
| `validate_swanlab_contracts.py` | 共用 | 基础设施 | 扫描 JSON/YAML 最终合同，并机械阻断尚未迁移的 SwanLab 入口 | 【已知锚点】任务简报直列 |

### 2.3 已否决（19 个，候选被实验或预注册门否决）

| 脚本名 | 章节 | 路线 | 用途 | 判据 |
| --- | --- | --- | --- | --- |
| `ch3_backbone_protocolA_v2.py` | 第三章 | 神经骨干消融 | 第三章基座对照（协议 A）v2：按骨干独立运行 + 断点续训 | 【负档0826】第一节"一维因果卷积/门控循环/全注意力（协议A-v2，四格齐备）"三条均"判据失败"，产物均已列入负结果档案不进正文；本工具是该三条结果的产出来源 |
| `ch3_full_mlp_independent_entity_head_s1.py` | 第三章 | RWKV-MLP | B10 冻结骨干上的三参数多算子实体头 S1 快速实验 | 【负档0826】"S1 线性实体头｜预注册否决｜`s1_source_rejected_keep_existing_O11`"；【恢复卡3】第四节"S1 已实现、运行并按预注册门源年否决" |
| `ch3_full_mlp_s0_precision_aggregation_diagnostic.py` | 第三章 | RWKV-MLP | 全容量多层感知机 S0 双精度×双聚合空间零训练诊断 | 【恢复卡3】"S0 固定 mean-max 与 S1 线性实体头均已源年否决"；本工具为 S0 候选族的诊断分支，随 S0 一并否决 |
| `ch3_full_mlp_strict_past_cpa_protocol_a_q0.py` | 第三章 | RWKV-MLP | 全容量 MLP 严格过去 CPA 协议 A Q0 | 【负档0826】"严格过去 CPA｜筛选否决｜源年 B10 0.9222/O11 0.7564 两格｜无完整四格"；【恢复卡3】第八节"不得重开的路径" |
| `ch3_full_mlp_valid_2x2_source_s0.py` | 第三章 | RWKV-MLP | 全容量 MLP 有效 2x2 的 LSPR23 零训练快速实验 | 【负档0826】"S0 固定 mean-max｜源年否决｜交互 −0.1548 强负"；【恢复卡3】"S0/S1……均已源年否决，只留过程文档，不进正文" |
| `ch3_full_mlp_valid_2x2_target_s0.py` | 第三章 | RWKV-MLP | 把已封印的有效 2x2 原样评价到 LSPR24，不训练、不选择 | 同上，S0 目标年评价分支，随 S0 一并否决 |
| `ch3_resmlp2_tabm_protocol_a_2x2.py` | 第三章 | 神经骨干消融 | ResMLP2 与 TabM4 的第三章协议 A 四格直接重跑入口 | 【负档0826】"ResMLP2｜协议否决｜当前配置不支持升级"（本脚本产出两骨干中 ResMLP2 分支为明确协议否决；TabM4 分支为"质量未排除……不否决模型族"，详见【恢复卡3】第三节，与 ResMLP2 结局不同，一并归入本档并在此注明差异） |
| `ch3_rwkv7_field_aware_protocol_a_2x2_bf16.py` | 第三章 | RWKV-其他骨干 | 固定 R2 与已封印容量的 RWKV-7 Protocol A 统一 BF16 重训入口 | 【负档0826】"CUDA-RWKV 四格｜判据失败……但四格检查点训练于自身门探针缺陷修复之前，缺陷未排除——FAIL 不构成机制失效的干净证据，也不能反推有效"——已被剔除出正文比较集，但非干净失效证据，此差异已在判据中注明 |
| `ch3_tabm32_paper_recipe_protocol_a.py` | 第三章 | 神经骨干消融 | TabM32 骨干专属论文配方协议 A 四格实验工具（任务 1 至 4） | 【负档0826】"TabM32（正式合同，四格齐备）｜判据失败｜0.7119/0.7034/0.5589/0.4558，两机制均负"；其 C00 检查点另被 `ch3_strong_backbone_scorelayer_backfill.py` 复用于重锚线分数层回填，机制挂载判据本身已否决 |
| `ch3_tabular_resnet_lspr24_inmemory_descriptive_eval.py` | 第三章 | 神经骨干消融 | 表格预归一化残差多层感知机四格在 LSPR24 上的零物化内存直读描述性评价 | 【快照0828】"ResNet 同源重评完成，X2 关闭（`996a18c`）：0.4317/0.6004/0.3487/0.4039——ELP 单开 +16.9 点为全项目最大单机制增益，CPA 负；判据 FAIL 留档" |
| `ch3_tabular_resnet_paper_recipe_protocol_a.py` | 第三章 | 神经骨干消融 | N14 表格预归一化残差多层感知机协议 A 四格生产入口 | 同上，为该骨干训练/资格封印入口，其产物最终判据 FAIL 留档不进正文 |
| `ch4_drift.py` | 第四章 | XGBoost | docstring 为 `ch3_full.py` 残留头（未更新）；实为第四章跨年度阈值失配诊断 v1 | 【恢复卡4】5.0 节"旧 `ch4-drift` v1 存在源内过拟合，相关读数全部失效，不得与 v2 混用" |
| `ch4_entity_uniform_direct_ap_q0.py` | 第四章 | RWKV-MLP(O11) | 第四章实体均匀训练与直接实体 AP 优化的冻结 Q0 入口 | 【恢复卡4】第六节"`COMPLETED_Q0_REJECTED`……`entity_uniform_measure_supported=false`、`direct_entity_ap_supported=false`" |
| `ch4_xgb_confidence_fallback_same_model_source_q0.py` | 第四章 | XGBoost | 机制二同模型三分、零训练源年修正 Q0 | 【恢复卡4】5.1 节"机械裁决为 `MECHANISM2_SAME_MODEL_SOURCE_Q0_REJECTED`" |
| `ch4_xgb_confidence_margin_fallback_same_model_source_q0.py` | 第四章 | XGBoost | 机制二同模型三分、风险余量阈值、零训练源年 Q0 | 【恢复卡4】5.1 节"机械裁决为 `MECHANISM2_CONFIDENCE_MARGIN_SAME_MODEL_SOURCE_Q0_REJECTED`" |
| `ch4_xgb_dtep_fixed_dyadic_q0.py` | 第四章 | XGBoost | 第四章 DTEP 固定二进多尺度 XGBoost 快速筛选 | 【恢复卡4】第四节"固定二进多尺度 DTEP 的源域三折实体 AP 差值……未通过预注册方向门，停止该候选" |
| `ch4_xgb_pbc_q0.py` | 第四章 | XGBoost | XGBoost 基座上的先导段预算标定零训练 Q0 | 【恢复卡4】第四节"无标签 BBSE-PBC……未产生方法增益，停止该候选" |
| `ch4_xgb_reflected_accumulation_joint_tong_same_model_source_q0.py` | 第四章 | XGBoost | 零训练检验原子分数反射累积与路径最大联合 Tong 控制 | 【快照0828】"M2 反射累积……机械裁决 `REJECTED_SOURCE_Q0`……反射累积为有效科学否决" |
| `ch3_cuda_rwkv_lspr24_inmemory_descriptive_eval.py` | 第三章 | RWKV-其他骨干 | 封印后 CUDA-RWKV 四格在 LSPR24 上的只读描述性评价（零训练、零物化） | 【负档0826】"CUDA-RWKV 四格｜判据失败｜C10−C00=−0.1811（≈5×SE）｜表示层 CPA 有害方向；但……缺陷未排除——FAIL 不构成机制失效的干净证据"——已被剔除出正文比较集，非干净证据的说明与上表 bf16 训练入口一致 |

### 2.4 历史（26 个，旧路线遗留，不再引用）

| 脚本名 | 章节 | 路线 | 用途 | 判据 |
| --- | --- | --- | --- | --- |
| `ch3_2x2_fairsel.py` | 第三章 | 神经骨干消融（旧协议） | 第三章 2x2 四格：修正后的检查点选择协议（LSPR23 实体不相交验证集逐 epoch 选优） | 【脚本互证】`ch3_baselines_full_merge.py` docstring："`ch3-2x2-fairsel/…json` 的 `cells.C11` 为旧的单 epoch argmax 协议数字，只作历史参照，协议与基线不一致" |
| `ch3_attribution.py` | 第三章 | 神经骨干消融（旧协议） | 第三章「实体级 CPA-ELP 输给 XGBoost 0.127」的归因诊断（E1/E2/E3/E6/E7） | 口径"逐字复刻 `ch3_full.py`"（旧协议冻结分数）；【脚本互证】`ch3_size_calib.py` docstring 指出"新协议换了检查点，实体 AP(max) 从 0.3858 掉到 0.2917……两个方向相反"，说明 0.127 差距分析针对已被替换的旧协议 |
| `ch3_backbone_2x2_local_screen.py` | 第三章 | 神经骨干消融 | 第三章 Transformer / GRU 双骨干四格本机筛选（screening_only） | docstring 自称"screening_only"筛选级；【快照0828】"CNN/GRU/Transformer 三骨干四格全 FAIL 剔除并立档（`d551b97`）"——服务器正式版 `ch3_backbone_protocolB_2x2_rerun.py` 已取代本机筛选阶段 |
| `ch3_backbone_protocolA.py` | 第三章 | 神经骨干消融 | 第三章基座对照（协议 A）：GRU / Transformer / 一维 CNN / RWKV-7 时间混合块各跑完整 2x2 四格 | `ch3_backbone_protocolA_v2.py` docstring："本文件由 `ch3_backbone_protocolA.py` 复制后**只增加持久化与运行编排**……v1 幸存的……已证明四个骨干实现正确……故 v2 不重写模型代码"——v1 已被 v2 取代 |
| `ch3_backbone_swap.py` | 第三章 | 神经骨干消融 | 第三章跨基座机制验证：把逐流编码器从 MLP 换成单层 GRU，重跑 C00 / C11 两格 | 单骨干替换验证，早于四骨干协议 A 系列；【负档0826】第一节已有更完整的"门控循环（协议A-v2）判据失败"记录取代本工具的探索性单骨干实验 |
| `ch3_e0_e8_audit.py` | 第三章 | 神经骨干消融（旧协议） | E0 并列/饱和审计 + E8 max 聚合专属配对自助 | docstring"独立审核（2026-08-17）指出诊断存在两个必须先封死的问题"，回应的是 `ch3_attribution.py` 旧协议 0.127 差距审计，随其一并归入历史 |
| `ch3_e5e6.py` | 第三章 | 神经骨干消融（旧协议） | 第三章 E5：序列长度 L 的敏感性实验（对齐 Dijk 2026 §5.9 训练协议） | docstring"模型固定为第三章最终方法 CPA-ELP，即 `ch3_full.py` 的 C11 格"——针对旧冻结协议的敏感性实验，协议已由 `ch3_hparam_fairsel_v2.py` 取代 |
| `ch3_e6.py` | 第三章 | 神经骨干消融（旧协议） | E6 攻击类别分面（独立后处理，消费冻结的 C11 分数） | docstring"直接消费 `ch3-full` 的 `scores_C11.npy`"——数据源为旧协议冻结分数 |
| `ch3_entity_key.py` | 第三章 | 神经骨干消融（旧协议） | 实体键对照：同一份冻结分数，只换分组键与聚合规则 | docstring"消费 `ch3-full` 的 `scores_C11.npy`"——数据源为旧协议冻结分数 |
| `ch3_gap_ci.py` | 第三章 | 神经骨干消融（旧协议） | XGBoost 与 CPA-ELP 实体级差距的配对自助置信区间 | docstring"回答一个问题：实体 AP 落后 0.0689、DR@4%FPR 落后 0.1210"——针对旧协议差距数值，新协议（`ch3_hparam_fairsel_v2.py`）后差距数值已变 |
| `ch3_grouping_recon.py` | 第三章 | 基础设施（一次性） | 分组粒度扫描的前置侦察：只读，确认三件事后才允许写正式扫描脚本 | docstring 自述"本文件是一次性侦察，跑完即删，不产生任何实验结论" |
| `ch3_hparam_fairsel.py` | 第三章 | 超参协议（旧版） | 第三章 CPA-ELP 超参搜索：合规选择协议下的 24 配置格点（只跑 C11 格） | `ch3_hparam_fairsel_v2.py` docstring："v1 把「top-5」实现成了**权重平均**……这与冻结脚本……实际做的事不同……本脚本改回预测平均" |
| `ch3_main.py` | 第三章 | 基础设施（早期副本） | 第三章双机制 2x2 交互实验（对齐 Dijk 2026 §5.9 训练协议）（docstring 与 `ch3_full.py` 相同） | 仅见于 `2026-08-13-会话交接文档.md` 等 08-13 期文档，早于当前主线协议（08-17 起）；`ch3_full.py` 为其后续冻结正式版 |
| `ch3_rwkv7_field_aware_protocol_a_2x2.py` | 第三章 | RWKV-其他骨干 | N-08：RWKV-7 字段感知输入选择与协议 A 单次四格（FP32 版本） | `ch3_rwkv7_field_aware_protocol_a_2x2_bf16.py` docstring："旧 FP32 运行只提供架构选择收据。本入口不复用旧模型、优化器、轮次选择或目标结果" |
| `ch3_tabular_resnet_lspr24_zero_train_descriptive_eval.py` | 第三章 | 神经骨干消融 | 表格预归一化残差多层感知机四格封印检查点的 LSPR24 零重训练描述性评价 | `ch3_tabular_resnet_lspr24_inmemory_descriptive_eval.py` docstring："上一轮运行 `ch3-tabular-resnet-lspr24-zero-train-descriptive-eval-v1` 即踩中该缺陷（读取 `dijk-repro/cache/X24.npy` 非 raw83 原值），本运行是它的更正重跑" |
| `ch4_paths.py` | 第四章 | 基础设施（早期副本） | docstring 与 `ch3_full.py` 相同（早期开发副本） | 仅见于 08-13 期文档（`2026-08-13-第四章提高实体AP候选调研-notes.md` 等），早于当前第四章主线 |
| `ch4_v2.py` | 第四章 | 基础设施（早期副本） | docstring 与 `ch3_full.py` 相同（早期开发副本） | 仅见于 08-13 期文档（`2026-08-13-超参设置证据台账.md` 等） |
| `ch4_xgb_confidence_fallback_source_q0.py` | 第四章 | XGBoost | 机制二源年三角色、零训练置信确认与源阈值回退 Q0 | 【恢复卡4】5.1 节"旧运行……的开发、校准与持出角色分数来自不同模型，故模型一致性不成立；其数值与否决裁决均无效，只保留为根因记录" |
| `ch4_xgb_two_stage_confidence_budget_q0.py` | 第四章 | XGBoost | 冻结 XGBoost 基座上的双段先导置信预算告警零训练 Q0 | 【恢复卡4】第一节"旧 `10%/10%/80%` 双段合同因选择和确认实体均为 0 而不可执行，已关闭" |
| `interact_2x2.py` | 第三章 | 基础设施（早期副本） | 第三章双机制 2x2 交互实验（预注册）（docstring 与 `ch3_full.py` 相同） | 仅见于 08-13 期文档 |
| `interact_dijk.py` | 第三章 | 基础设施（早期副本） | 第三章双机制 2x2 交互实验（对齐 Dijk 2026 §5.9 训练协议）（docstring 与 `ch3_full.py` 相同） | 仅见于 08-13 期文档 |
| `interact_final.py` | 第三章 | 基础设施（早期副本） | 第三章双机制 2x2 交互实验（预注册）（docstring 与 `ch3_full.py` 相同） | 仅见于 08-13 期文档 |
| `mech_ablate.py` | 共用 | RWKV 训练路径（历史实现） | RWKV-7 机制单因子消融（每档只对 B 改一处）：每档只加一个机制，定位增益/损害的来源 | `.Codex/docs/RWKV/AGENTS.md`"历史 RWKV 训练实现、权重、断点或速度基线；活动路径只认独立 CUDA 融合、合法 Raw83 和从头训练"——本脚本为纯 PyTorch 机制阶梯消融，非独立 CUDA 融合实现 |
| `r2_final_sidecar_candidate_materialize.py` | 历史 | PINN-R2 历史 | 无模块 docstring；模块常量 `GENIS_NAMESPACE = "dataset-candidate-genis-v0"` 表明是 GeNIS 候选侧车数据物化工具 | 【恢复卡3】第八节"不得重开的路径……GeNIS 的当前 Q0；均不重启、不追调，也不写成正式证伪" |
| `r2_quic_seed_partition_materialize.py` | 历史 | PINN-R2 历史 | 冻结 QUIC 种子连接分区及连续四窗构造合同 | 文件名前缀 `r2_`（对应 PINN/R2 历史路线）+ QUIC/ns3 语境，属历史 R2 路线数据物化工具，非当前 RWKV 路线制品 |
| `r2_quic_seed_window_materialize.py` | 历史 | PINN-R2 历史 | 将通过审计的 QUIC qlog 物化为零权重的固定因果窗种子真值 | 同上 |

### 2.5 未确认（7 个，需人工裁定）

| 脚本名 | 章节 | 路线 | 用途 | 未能确认的原因 |
| --- | --- | --- | --- | --- |
| `ch3_auxw_sweep.py` | 第三章 | RWKV-MLP（超参敏感性） | 第三章 CPA-ELP 训练配置扫描：辅助损失权重、辅助损失粒度、训练采样单元 | 七个变体（AUX_W 网格 / 实体级辅助损失 / 实体分层采样）在四份主控文档中均未见结果或采纳记录 |
| `ch3_cnn_backbone_2x2.py` | 第三章 | 神经骨干消融 | 第三章 卷积骨干 + 两机制 2×2：在赢过本方法的等参数一维卷积基线上做纯机制消融 | 有对应实施计划 `2026-08-18-卷积骨干加两机制的实施计划.md`，但【负档0826】第一/二节均未列出该实验的结论行（既非"进正文"也未见明确 FAIL 记录），运行结果状态不明 |
| `ch3_env_probe.py` | 第三章 | 数据探索 | 探针：LSPR23 内部是否存在可用作「多源环境」的划分依据 | 四份主控文档均未提及该探针的判据结果（三条判据是否满足）或后续采纳情况 |
| `ch3_grande_lspr24_zero_train_descriptive_eval.py` | 第三章 | GRANDE | GRANDE G-A/G-B 封印检查点的 LSPR24 零重训练描述性评价 | 【负档0826】"GRANDE｜证据不足｜G-A/G-B 实体 AP `0.5453/0.4386`，仅 `20` 个正实体｜实验待证，G-B 身份漂移不可恢复"——明确既未通过也未被否决，状态为"实验待证"，不落入 已否决/历史 任一清晰桶 |
| `ch3_grande_protocol_a_source_q0.py` | 第三章 | GRANDE | GRANDE 可微树骨干 LSPR23 协议 A 源年 Q0 | 同上，为 GRANDE 训练入口，其后续评价结论同样标"实验待证" |
| `ch3_size_calib.py` | 第三章 | RWKV-MLP（旧协议重测） | 路径 B 前置确认：新协议下规模膨胀是否仍然存在，以及规模校准能否让实体 AP 超越基线 | docstring 自述用新协议分数重测旧诊断结论，但四份主控文档未见其重测结论是否成立的记录 |
| `ch4_mlp_o11_operator_oracle_e0_local_screen.py` | 第四章 | RWKV-MLP(O11) | 第四章 E0 本机筛选：多聚合算子 oracle 上界诊断（screening_only） | 【快照0828】"在飞任务……E0 oracle 存废实验：死亡时 `--construction e0` 分支未实现（工具只有 a/b/c 分支）……按用户「先聚焦第三章」裁决暂缓，不重派；第三章机制定型后随第四章续办"——明确处于暂缓/搁置状态，既非活跃推进也非否决或历史 |

## 三、统计小结

### 3.1 按状态计数

| 状态 | 数量 |
| --- | --- |
| 活跃 | 35 |
| 基础设施 | 35 |
| 已否决 | 19 |
| 历史 | 26 |
| 未确认 | 7 |
| **合计** | **122** |

> 核对：35+35+19+26+7 = 122，与顶层目录实测的 `.py` 文件数（122 个，见文档开头
> 「范围」说明）逐行对齐，第二节五张分表共 122 行、每个脚本文件名恰好出现一次，
> 无遗漏、无重复计数。

### 3.2 按路线计数（以第二节表格「路线」列归并）

| 路线 | 数量 | 说明 |
| --- | --- | --- |
| RWKV-FT | 9 | `ch3_ft_*` 系列（活跃） |
| RWKV-MLP | 15 | `ch3_full_mlp_*`、`ch4_mlp_o11_*` 等（含活跃、已否决、未确认） |
| RWKV-其他骨干 | 6 | CUDA-RWKV、TabM、ResNet、ResMLP2 等跨骨干消融（含已否决、历史） |
| XGBoost（第三/四章机制载体） | 15 | `ch3_xgb_*`、`ch4_xgb_*` 系列 |
| 神经骨干消融（通用协议 A/B） | 9 | `ch3_backbone_*`、`ch3_baselines_*`、`ch3_cnn_backbone_2x2.py`、`ch3_resmlp2_tabm_protocol_a_2x2.py` 等 |
| GRANDE | 3 | `ch3_grande_*` 系列 |
| PINN-R2 历史 | 3 | `r2_*` 系列 |
| 基础设施（共用/远程/精度/校验/早期副本） | 62 | 见第二节"基础设施""历史"两节中标注"共用"或"（早期副本）"的条目，以及各章节内部的诊断/资格门工具 |

上表按第二节表格「路线」列的字面标注人工归并，允许与 3.1 节状态计数存在交叉重复
（同一脚本在"路线"与"状态"两个维度各计一次，二者不是同一划分体系，不可相加对比）。

## 四、未确认清单（需人工裁定，共 7 项）

1. `ch3_auxw_sweep.py`
2. `ch3_cnn_backbone_2x2.py`
3. `ch3_env_probe.py`
4. `ch3_grande_lspr24_zero_train_descriptive_eval.py`
5. `ch3_grande_protocol_a_source_q0.py`
6. `ch3_size_calib.py`
7. `ch4_mlp_o11_operator_oracle_e0_local_screen.py`

以上 7 项的共同特征是：四份主控文档（两张恢复卡、全局进度快照、第三章跨骨干负结果档案）
均未给出明确的"通过/否决/取代"结论，多数属于"实验待证""结果状态未记录"或"用户裁决暂缓"。
若需要推进这些候选的存废裁决，应先按 `AGENTS.md` 的"研究证据顺序"要求，
检索是否存在未被本次四份文档覆盖的更细粒度报告（如 `.Codex/docs/RWKV/` 下以对应
运行身份命名的实施计划/实施报告），而不是仅凭脚本 docstring 或文件名臆断状态。
