# tools/ 索引

> **本文件由 `tools/tools_index.py` 生成，请勿手改。** 分组规则错了改生成器、
> 重新运行 `/opt/miniconda3/envs/rwkv/bin/python tools/tools_index.py` 后
> 重新提交——手改的内容会在下次生成时被覆盖丢失。

## 为什么 tools/ 是扁平的

`tools/` 下的脚本靠裸 `import ch3_xxx` 这类写法互相引用，依赖 Python 把脚本所在
目录（`tools/`）自动加入 `sys.path`；一旦把文件移进子目录，这类导入会全线断裂。
同时，27 份冻结实验配置里记录了 `base.tool_path` 与 `tool_sha256`——文件一动，
路径和内容哈希都变了，已有运行制品就没法再溯源到当初实际执行的代码，而四格实验
即将启动。**这两条决定了 tools/ 现在只能加索引，不能重组**；重组要等四格实验跑
完、单独立项评估依赖图后再做。

## 分组规则说明

角色判定顺序：一次性审计 → 诊断探针 → 评价与指标 → 数据物化与视图 → 兜底
（按"是否可执行"分训练入口 / 机制实现）。关键词只匹配"文件名 + docstring 首句"，
不用整份 docstring——实测扩大到全文后 `eval`/`诊断` 等词会命中背景说明段落里的
无关提及，误伤了不少文件；首句是作者自己写的摘要，信噪比更高。

"可执行入口"不是单看 `if __name__ == "__main__"`：仓库里有一批历史脚本
（如 `ch3_backbone_protocolA.py`）写成"从上到下线性执行、没有 `__main__` 守卫"，
import 即执行，判定用的是"有守卫，或模块顶层有 ≥3 条非简单赋值的实质执行语句"。
这套组合规则是启发式的，边界情形（例如同时符合两种角色描述的脚本）按更具体的
关键词优先，具体清单见生成器源码顶部的注释；分组明显错误的按生成器规则调整后
重新生成，不要手改本文件。


## 当前规模统计

- 顶层 `.py` 文件：144 个，共 110125 行
- 顶层文件中无 docstring：1 个
- 子目录：9 个
- 顶层角色计数：训练入口 73、机制实现 5、评价与指标 16、数据物化与视图 6、诊断探针 24、远程与运维 0、一次性审计 20
  - `.claude/`：2 个文件（.py 0）
  - `_resume_audit/`：5 个文件（.py 1）
  - `ch3_final_weights_assets/`：2 个文件（.py 1）
  - `dijk2026_replication/`：15 个文件（.py 6）
  - `env/`：1 个文件（.py 0）
  - `lspr24_g0/`：48 个文件（.py 0）
  - `r2_genis_totbytes_verifier/`：12 个文件（.py 0）
  - `r2_quic_qlog_audit/`：3 个文件（.py 0）
  - `remote_exec/`：3 个文件（.py 0）

## 顶层模块索引（按角色分组）

### 训练入口（73）

| 文件 | 行数 | 可执行入口 | 说明 |
|---|---:|---|---|
| `ch3_2x2_fairsel.py` | 428 | 是 | 第三章 2x2 四格：修正后的检查点选择协议（LSPR23 实体不相交验证集逐 epoch 选优）。 |
| `ch3_auxw_sweep.py` | 442 | 是 | 第三章 CPA-ELP 训练配置扫描：辅助损失权重、辅助损失粒度、训练采样单元。 |
| `ch3_backbone_2x2_local_screen.py` | 722 | 是 | 第三章 Transformer / GRU 双骨干四格本机筛选（screening_only）。 |
| `ch3_backbone_protocolA.py` | 826 | 是 | 第三章基座对照（协议 A）：GRU / Transformer / 一维 CNN / RWKV-7 时间混合块各跑完整 2x2 四格。 |
| `ch3_backbone_protocolA_v2.py` | 876 | 是 | 第三章基座对照（协议 A）v2：**按骨干独立运行 + 断点续训**。 |
| `ch3_backbone_protocolB_2x2_rerun.py` | 917 | 是 | 第三章基座消融协议 B：全注意力（transformer）与门控循环（gru）重跑。 |
| `ch3_backbone_swap.py` | 675 | 是 | 第三章跨基座机制验证：把逐流编码器从 MLP 换成单层 GRU，重跑 C00 / C11 两格。 |
| `ch3_baselines_full_merge.py` | 129 | 是 | 第三章基线重跑的合并与主比较表生成。 |
| `ch3_baselines_full_neural.py` | 543 | 是 | 第三章已发表基线重跑（神经模型族）：GRU + 全注意力 Transformer + 一维 CNN，全量冻结缓存。 |
| `ch3_baselines_full_trees.py` | 428 | 是 | 第三章已发表基线重跑（树模型族）：随机森林 + XGBoost，全量冻结缓存。 |
| `ch3_baselines_param_matched.py` | 645 | 是 | 第三章已发表基线的**等参数预算**重跑：GRU + 全注意力 Transformer + 一维 CNN，全量冻结缓存。 |
| `ch3_cnn_backbone_2x2.py` | 1726 | 是 | 第三章 卷积骨干 + 两机制 2×2：在赢过本方法的等参数一维卷积基线上做纯机制消融。 |
| `ch3_e5e6.py` | 363 | 是 | 第三章 E5：序列长度 L 的敏感性实验（对齐 Dijk 2026 §5.9 训练协议）。 |
| `ch3_e6.py` | 116 | 是 | E6 攻击类别分面（独立后处理，消费冻结的 C11 分数）。 |
| `ch3_entity_key.py` | 117 | 是 | 实体键对照：同一份冻结分数，只换分组键与聚合规则。 |
| `ch3_fairsel_xgb_matched.py` | 103 | 是 | 把 XGBoost 基线的 Lp 聚合口径对齐到新协议 C11 学到的 p，做同 p 比较。 |
| `ch3_ft_c00_dual_selection.py` | 3784 | 是 | 裸 FT C00 的跨设备双选轮训练与真实运行校准。 |
| `ch3_ft_entity_memory_interface.py` | 262 | 是 | 机制一（因果实体记忆交叉注意力）严格过去接口构建器。 |
| `ch3_ft_entity_ranking_loss.py` | 1474 | 是 | 机制二：实体路径最大分数与多预算 CVaR-pAUC 排序损失（spec 5.1、5.3、5.3.1）。 |
| `ch3_ft_entity_stratified_sampler.py` | 328 | 是 | 机制二：实体分层采样器（spec 5.4 节「每步按实体均匀抽正实体与负实体」）。 |
| `ch3_ft_execution_path_receipt.py` | 420 | 是 | 四格执行路径观测层：记录每个前向调用点的实际调用对象、Dynamo 编译统计与图断裂位置。 |
| `ch3_ft_gradient_controller.py` | 276 | 是 | 机制二：梯度控制器——单向 PCGrad 投影 + 范数上限（spec 5.5 节）。 |
| `ch3_ft_transformer_field_token_protocol_a.py` | 5180 | 是 | FT-Transformer 逐字段 Token 协议 A 四格实验工具（任务 1 至 5）。 |
| `ch3_full.py` | 315 | 是 | 第三章双机制 2x2 交互实验（对齐 Dijk 2026 §5.9 训练协议）。 |
| `ch3_full_capacity_mlp_source_screen.py` | 1192 | 是 | 第三章全容量多层感知机的 LSPR23 C00 容量与配方筛选入口。 |
| `ch3_full_mlp_complete_entity_lp_protocol_a_q0.py` | 1772 | 是 | 全容量 MLP 完整实体幂平均协议 A Q0。 |
| `ch3_full_mlp_complete_entity_lp_protocol_a_q0_bf16.py` | 1108 | 是 | 全容量多层感知机统一 BF16 协议 A 资格实验。 |
| `ch3_full_mlp_independent_entity_head_s1.py` | 403 | 是 | B10 冻结骨干上的三参数多算子实体头 S1 快速实验。 |
| `ch3_full_mlp_strict_past_cpa_protocol_a_q0.py` | 1232 | 是 | 全容量 MLP 严格过去 CPA 协议 A Q0。 |
| `ch3_full_mlp_valid_2x2_source_s0.py` | 487 | 是 | 全容量 MLP 有效 2x2 的 LSPR23 零训练快速实验。 |
| `ch3_full_mlp_valid_2x2_target_s0.py` | 261 | 是 | 把已封印的有效 2x2 原样评价到 LSPR24，不训练、不选择。 |
| `ch3_grande_protocol_a_source_q0.py` | 2314 | 是 | GRANDE 可微树骨干 LSPR23 协议 A 源年 Q0。 |
| `ch3_hparam_fairsel.py` | 612 | 是 | 第三章 CPA-ELP 超参搜索：合规选择协议下的 24 配置格点（只跑 C11 格 agg=True, lp=True）。 |
| `ch3_hparam_fairsel_v2.py` | 853 | 是 | 第三章 CPA-ELP：统一「top-5 预测平均」检查点策略下的 24 配置超参搜索 + 2x2 四格重跑。 |
| `ch3_main.py` | 309 | 是 | 第三章双机制 2x2 交互实验（对齐 Dijk 2026 §5.9 训练协议）。 |
| `ch3_neural_backbone_source_oof_gate.py` | 2109 | 是 | 第三章神经骨干源年实体三折折外资格门。 |
| `ch3_p1_strata.py` | 103 | 是 | P1 第 1 步：在 LSPR23 实体不相交验证集上统计实体流数分布，确认难分层是否可用。 |
| `ch3_resmlp2_tabm_protocol_a_2x2.py` | 1253 | 是 | ResMLP2 与 TabM4 的第三章协议 A 四格直接重跑入口。 |
| `ch3_rwkv7_cpa_elp_source_oof_gate.py` | 1072 | 是 | 第三章 RWKV-7 与 CPA/ELP 源年实体三折折外资格门。 |
| `ch3_rwkv7_field_aware_protocol_a_2x2.py` | 2344 | 是 | N-08：RWKV-7 字段感知输入选择与协议 A 单次四格。 |
| `ch3_rwkv7_field_aware_protocol_a_2x2_bf16.py` | 2202 | 是 | 固定 R2 与已封印容量的 RWKV-7 Protocol A 统一 BF16 重训入口。 |
| `ch3_rwkv_cuda_self_gate.py` | 1069 | 是 | CUDA-RWKV 小型容量自身资格门。 |
| `ch3_size_calib.py` | 166 | 是 | 路径 B 前置确认：新协议下规模膨胀是否仍然存在，以及规模校准能否让实体 AP 超越基线。 |
| `ch3_strong_backbone_scorelayer_backfill.py` | 493 | 是 | 把分数层 CPA-ELP 四格移植到 FT-Transformer 与 TabM32 的冻结 C00 逐流分数上。 |
| `ch3_tabm32_paper_recipe_protocol_a.py` | 3560 | 是 | TabM32 骨干专属论文配方协议 A 四格实验工具（任务 1 至 4）。 |
| `ch3_tabm_cpa_elp_source_oof_gate.py` | 732 | 是 | 第三章 TabM 式骨干源年实体三折折外资格门。 |
| `ch3_tabular_resnet_paper_recipe_protocol_a.py` | 1117 | 是 | N14 表格预归一化残差多层感知机协议 A 四格生产入口。 |
| `ch3_xgb_cpa_elp_entity_oof.py` | 1703 | 是 | 第三章 XGBoost 适配 CPA 与 ELP：源年实体折外选择和目标年四格评价。 |
| `ch4_drift.py` | 276 | 是 | 第三章双机制 2x2 交互实验（对齐 Dijk 2026 §5.9 训练协议）。 |
| `ch4_e1_source_entity_oof_gate.py` | 1521 | 是 | 第四章 E1 源年实体三折折外信号快速门禁。 |
| `ch4_entity_uniform_direct_ap_q0.py` | 1989 | 是 | 第四章实体均匀训练与直接实体 AP 优化的冻结 Q0 入口。 |
| `ch4_mlp_o11_oof_fold_models_local_screen.py` | 320 | 是 | 第四章 D0 本机筛选支线：全容量 MLP O11 三折折外模型（screening_only）。 |
| `ch4_mlp_o11_stratified_tong_2x2_local_screen.py` | 978 | 是 | 第四章 S_a/S_b 本机筛选：MLP 底座长度分层 Tong 证书 2×2 消融（screening_only）。 |
| `ch4_mlp_o11_tong_pooled_q0_local_screen.py` | 482 | 是 | 第四章 M1' 本机筛选：MLP 底座池化 Tong 路径最大证书（screening_only）。 |
| `ch4_paths.py` | 365 | 是 | 第三章双机制 2x2 交互实验（对齐 Dijk 2026 §5.9 训练协议）。 |
| `ch4_v2.py` | 330 | 是 | 第三章双机制 2x2 交互实验（对齐 Dijk 2026 §5.9 训练协议）。 |
| `ch4_xgb_confidence_fallback_same_model_source_q0.py` | 494 | 是 | 机制二同模型三分、零训练源年修正 Q0。 |
| `ch4_xgb_confidence_fallback_source_q0.py` | 1114 | 是 | 机制二源年三角色、零训练置信确认与源阈值回退 Q0。 |
| `ch4_xgb_confidence_margin_fallback_same_model_source_q0.py` | 583 | 是 | 机制二同模型三分、风险余量阈值、零训练源年 Q0。 |
| `ch4_xgb_dtep_fixed_dyadic_q0.py` | 1450 | 是 | 第四章 DTEP 固定二进多尺度 XGBoost 快速筛选。 |
| `ch4_xgb_entity_path_max_np_q0.py` | 619 | 是 | 用源年折外实体路径最大统计量执行零训练 Q0。 |
| `ch4_xgb_path_max_tong_final_model_source_seed42.py` | 1328 | 是 | 训练种子 42 最终单模型并执行源年实体路径最大 Tong 六臂评价。 |
| `ch4_xgb_pbc_q0.py` | 1526 | 是 | XGBoost 基座上的先导段预算标定零训练 Q0。 |
| `ch4_xgb_reflected_accumulation_joint_tong_same_model_source_q0.py` | 1891 | 是 | 零训练检验原子分数反射累积与路径最大联合 Tong 控制。 |
| `ch4_xgb_two_stage_confidence_budget_q0.py` | 1419 | 是 | 冻结 XGBoost 基座上的双段先导置信预算告警零训练 Q0。 |
| `cuda_rwkv_official_backend.py` | 803 | 是 | 独立 CUDA-RWKV 官方融合后端。 |
| `interact_2x2.py` | 310 | 是 | 第三章双机制 2x2 交互实验（预注册）。 |
| `interact_dijk.py` | 371 | 是 | 第三章双机制 2x2 交互实验（对齐 Dijk 2026 §5.9 训练协议）。 |
| `interact_final.py` | 323 | 是 | 第三章双机制 2x2 交互实验（预注册）。 |
| `mech_ablate.py` | 286 | 是 | RWKV-7 机制单因子消融（每档只对 B 改一处）：每档只加一个机制，定位增益/损害的来源。 |
| `rwkv7_k0_fused_backend.py` | 351 | 是 | RWKV-7 K0 基础 WKV CUDA 融合后端。 |
| `select_signal.py` | 351 | 是 | 第三章双机制 2x2 交互实验（对齐 Dijk 2026 §5.9 训练协议）。 |
| `tools_index.py` | 503 | 是 | tools/ 目录索引生成器：只读扫描本目录，把结果写成 tools/INDEX.md。 |

### 机制实现（5）

| 文件 | 行数 | 可执行入口 | 说明 |
|---|---:|---|---|
| `ch3_backbone_models.py` | 347 | 否 | 第三章基座骨干共享定义：从 tools/ch3_backbone_protocolA_v2.py 抽取，供协议 A/B 等多个入口 import 复用。 |
| `ch3_ft_causal_entity_memory.py` | 365 | 否 | 机制一（因果实体记忆交叉注意力）：记忆状态容器与交叉注意力模块。 |
| `ch3_ft_entity_bce.py` | 155 | 否 | 四格消融共同底座：实体级 BCE 损失（不接入宿主，独立模块）。 |
| `ch3_ft_entity_gated_ple.py` | 282 | 否 | M-E｜实体门控的分段线性数值分词：PLE 编码、箱边界拟合与门控分词器。 |
| `ch3_ft_entity_segment_state.py` | 77 | 否 | M-E 严格过去实体状态的预计算与归一化常数拟合。 |

### 评价与指标（16）

| 文件 | 行数 | 可执行入口 | 说明 |
|---|---:|---|---|
| `ch3_alert_budget_curves.py` | 391 | 是 | 告警预算曲线重分析：对已落盘的 LSPR24 逐流分数重新计算实体级检出率随假阳率的曲线、 前 k 个实体的精确率与曲线交叉点。 |
| `ch3_build_metrics_table.py` | 2291 | 是 | 从第三章原始运行制品机械生成统一指标总表。 |
| `ch3_common_first_alert_fp_budget_envelope.py` | 2940 | 是 | 五个既有系统在 LSPR24 上的共同实际首次告警 FP 预算包络。 |
| `ch3_crossyear_f1_column.py` | 382 | 是 | 跨年 F1 列计算：从既有 first-alert / FP-预算包络制品纯重算实体级 F1， 作为统一总表的新增一列，用于与同数据集已发表工作（如 Leoste 2025）在 F1 口径上直接对位。 |
| `ch3_cuda_rwkv_lspr24_inmemory_descriptive_eval.py` | 1036 | 是 | 封印后 CUDA-RWKV 四格在 LSPR24 上的只读描述性评价（零训练、零物化）。 |
| `ch3_ft_c00_lspr24_descriptive_eval.py` | 20 | 是 | FT C00 selected-by-entity 的独立 LSPR24 零训练描述性评价入口。 |
| `ch3_ft_c01_c10_lspr24_descriptive_eval.py` | 940 | 是 | FT C01/C10 在 LSPR24 上的提前零训练描述性评价。 |
| `ch3_ft_lspr24_descriptive_eval.py` | 1428 | 是 | CEM-BER 四格在 LSPR24 上的封印后描述性评价。 |
| `ch3_gap_ci.py` | 118 | 是 | XGBoost 与 CPA-ELP 实体级差距的配对自助置信区间。 |
| `ch3_grande_lspr24_zero_train_descriptive_eval.py` | 721 | 是 | GRANDE G-A/G-B 封印检查点的 LSPR24 零重训练描述性评价。 |
| `ch3_published_neural_operational_backfill.py` | 1019 | 是 | 用已持久化分数回填三种已发表神经基线的目标年运营指标。 |
| `ch3_tabular_resnet_lspr24_inmemory_descriptive_eval.py` | 1270 | 是 | 表格预归一化残差多层感知机四格在 LSPR24 上的零物化内存直读描述性评价。 |
| `ch3_tabular_resnet_lspr24_zero_train_descriptive_eval.py` | 780 | 是 | 表格预归一化残差多层感知机四格封印检查点的 LSPR24 零重训练描述性评价。 |
| `ch3_xgb_cpa_elp_eval_continuation.py` | 834 | 是 | 从已冻结的源年模型接续 XGBoost+CPA+ELP 的 LSPR24 评价。 |
| `ch3_xgb_cpa_elp_operational_backfill.py` | 1325 | 是 | 为冻结 XGBoost＋CPA-ELP C11 回填完整目标年运营指标。 |
| `ch3_xgb_entity.py` | 191 | 是 | XGBoost 基线的实体级评价，与冻结 C11 逐字对齐。 |

### 数据物化与视图（6）

| 文件 | 行数 | 可执行入口 | 说明 |
|---|---:|---|---|
| `ch3_final_weights_freeze.py` | 645 | 是 | 第三章定稿模型权重固化（协议 A 四格重跑 + 逐位复现校验 + 归档打包）。 |
| `ch3_protocol_a_raw83_prepare.py` | 1023 | 是 | Protocol A Raw83 共享预处理 P0–P5 幂等阶段入口。 |
| `ch4_mlp_o11_oof_fold_models.py` | 297 | 是 | 第四章 D0：全容量 MLP O11 配置的源年三折折外评分模型物化。 |
| `r2_final_sidecar_candidate_materialize.py` | 1163 | 是 | （无 docstring，见下方待补清单） |
| `r2_quic_seed_partition_materialize.py` | 238 | 是 | 冻结 QUIC 种子连接分区及连续四窗构造合同。 |
| `r2_quic_seed_window_materialize.py` | 729 | 是 | 将通过审计的 QUIC qlog 物化为零权重的固定因果窗种子真值。 |

### 诊断探针（24）

| 文件 | 行数 | 可执行入口 | 说明 |
|---|---:|---|---|
| `ch3_attribution.py` | 557 | 是 | 第三章「实体级 CPA-ELP 输给 XGBoost 0.127」的归因诊断（E1/E2/E3/E6/E7）。 |
| `ch3_backbone_gru_precision_probe.py` | 90 | 是 | 只读诊断：判定「打包批前向 vs 逐条截断前向」的 2.4e-4 差异来自 TF32 精度还是掩码错误。 |
| `ch3_crossL_fair_val.py` | 271 | 是 | 诊断（不改变任何已冻结的选择，不触碰 LSPR24）：跨 L 排序是不是验证集口径漂移的产物。 |
| `ch3_env_probe.py` | 117 | 是 | 探针：LSPR23 内部是否存在可用作「多源环境」的划分依据。 |
| `ch3_ft_compile_equivalence_probe.py` | 215 | 是 | torch.compile 对 FT 主干的逐位等价与提速探针。 |
| `ch3_ft_data_path_benchmark.py` | 172 | 是 | FT 训练数据路径耗时基准：量化「X23 显存常驻」的收益上限。 |
| `ch3_ft_entity_bce_weight_calibration.py` | 203 | 是 | 实体级 BCE 权重 w_e 的零训练诊断标定。 |
| `ch3_ft_entity_state_carrier_probe.py` | 150 | 是 | M-E 状态载体候选诊断：只用 LSPR23，判断哪些严格过去可观测量值得进入 s_e。 |
| `ch3_ft_entity_tail_aggregation_probe.py` | 602 | 是 | 实体内尾部聚合（经验 CVaR_α，ATk 形式）的源年零训练重聚合诊断。 |
| `ch3_ft_me_gate_scope_probe.py` | 288 | 是 | M-E 门作用域诊断：量化 𝟙[c≥1] 让多少样本、多少实体真正受机制影响。 |
| `ch3_ft_target_entity_prior_probe.py` | 182 | 是 | 目标年「纯流数先验」基线探测：不加载模型、不做前向、不读检查点。 |
| `ch3_full_mlp_s0_precision_aggregation_diagnostic.py` | 2600 | 是 | 全容量多层感知机 S0 双精度×双聚合空间零训练诊断。 |
| `ch3_gradient_controller_conflict_probe.py` | 302 | 是 | 机制二梯度控制器冲突实测：在已收敛模型上量 ‖g_f‖ 与 ‖g_r‖。 |
| `ch3_hparam_probe.py` | 71 | 是 | 超参搜索的规模探针：只读 LSPR23 侧，估算各 L 的序列数、切分规模与步数预算。 |
| `ch3_lspr23_entity_history_availability.py` | 217 | 是 | 第三章 LSPR23 实体历史可用性诊断：为因果实体记忆机制提供动机与作用面证据。 |
| `ch3_rwkv7_k0_fused_benchmark.py` | 958 | 是 | RWKV-7 K0 纯 PyTorch 与 CUDA 融合核等价性和速度基准。 |
| `ch3_trunc_probe.py` | 135 | 是 | P2 可行性探针：1e-7 截断是否真的压住了实体 AP。 |
| `ch4_entity_length_bucket_diagnostic.py` | 1199 | 是 | 重跑第三章四格并诊断第四章实体流数分桶。 |
| `ch4_mlp_o11_crossyear_threshold_transfer_diag.py` | 387 | 是 | 第四章跨年阈值迁移诊断：MLP O11 底座源年校准阈值搬到 LSPR24 的失配幅度存在性诊断。 |
| `ch4_mlp_o11_operator_oracle_e0_local_screen.py` | 432 | 是 | 第四章 E0 本机筛选：多聚合算子 oracle 上界诊断（screening_only）。 |
| `ch4_mlp_o11_pathology_diagnostics_local_screen.py` | 326 | 是 | 第四章 D1/D2 本机筛选：MLP 底座曝光病灶与长度桶条件风险再确认。 |
| `ch4_xgb_entity_exposure_lesion_source_diagnostic.py` | 1217 | 是 | 零训练诊断实体重复曝光是否同时造成误报突破与迟到正检出。 |
| `ch4_xgb_long_entity_bucket_diagnostic.py` | 536 | 是 | 零重训诊断 XGBoost 在 LSPR24 长实体上的四格收益方向。 |
| `ch4_xgb_path_risk_length_bucket_source_diagnostic.py` | 1066 | 是 | 按冻结长度桶诊断源年实体路径最大风险，不训练新模型。 |

### 远程与运维（0）

（本层无此角色文件）

### 一次性审计（20）

| 文件 | 行数 | 可执行入口 | 说明 |
|---|---:|---|---|
| `_tmp_measure_we_probe_costs.py` | 328 | 是 | 一次性本机 CPU 测量脚本（用完即删，不进入生产代码）。 |
| `build_ch3_xgb_parent_recovery_proof.py` | 248 | 是 | 为中断的第三章 XGBoost 父运行生成独立恢复证明。 |
| `ch3_backbone_read_mlp_ref.py` | 33 | 是 | 只读：打印 ch3-hparam-fairsel-v2（top-5 预测平均协议）的 2x2 四格 LSPR24 指标。 |
| `ch3_cuda_rwkv_raw83_qualification.py` | 2870 | 是 | 独立 CUDA-RWKV Raw83 资格单入口。 |
| `ch3_e0_e8_audit.py` | 151 | 是 | E0 并列/饱和审计 + E8 max 聚合专属配对自助。 |
| `ch3_fairsel_apicheck.py` | 59 | 是 | ch3_2x2_fairsel.py 用到的、相对 ch3_full.py 新增的 PyTorch 接口的运行时核验。 |
| `ch3_ft_emit_four_cell_summary.py` | 333 | 是 | 第三章 FT 四格读数汇总：把四个格的选轮收据压成一份可随时回传的小 JSON。 |
| `ch3_ft_tier_identity.py` | 131 | 是 | 起跑前的档位身份并排核对：防止把本机档、缩容档、满血档跑混。 |
| `ch3_ft_verify_four_cell_artifacts.py` | 310 | 是 | CEM-BER 四格制品完整性与可复核性核验。 |
| `ch3_grande_swanlab_publish_repair.py` | 868 | 是 | 只读绑定 GRANDE 已完成制品并修复 SwanLab 聚合指标发布。 |
| `ch3_grouping_recon.py` | 68 | 是 | 分组粒度扫描的前置侦察：只读，确认三件事后才允许写正式扫描脚本。 |
| `ch3_lspr23_field_cardinality_receipt.py` | 392 | 是 | 生成 LSPR23 Protocol A 训练区七个字段的只读基数收据。 |
| `ch3_sortkey_audit.py` | 91 | 是 | 序列排序键只读核实：判定 dijk-repro 缓存里的 I23/I24/T23 用的是哪个时间字段。 |
| `ch3_sortkey_audit2.py` | 64 | 是 | 序列排序键核实第二部分：量化按起始时间排序带来的因果性偏差（只读，不占 GPU）。 |
| `ch3_sortkey_audit3.py` | 59 | 是 | 序列排序键核实第三部分：按位置统计前缀里的"未来完成流"（只读，不占 GPU）。 |
| `ch3_sortkey_audit4.py` | 73 | 是 | 序列排序键核实第四部分：把同一组判据补到训练年度 LSPR23（只读，不占 GPU）。 |
| `ch3_valset_crossL_audit.py` | 100 | 是 | 只读诊断：24 配置跨 L 排序时，LSPR23 验证集的**逐流集合**在 L=32/64/128 下是否相同。 |
| `neural_precision_runtime.py` | 737 | 是 | 单卡神经训练精度、等效微批量与资源收据共享脚手架。 |
| `selftest_ch4.py` | 86 | 是 | 三条路径的逻辑自检：在已知真值的合成数据上验证公式实现是否正确。 |
| `validate_swanlab_contracts.py` | 280 | 是 | 扫描 JSON/YAML 最终合同，并机械阻断尚未迁移的 SwanLab 入口。 |

## 无 docstring 文件（待补充，1 个）

- `r2_final_sidecar_candidate_materialize.py`

## 子目录

### .claude/

文件数：2（.py 0 个，其他 2 个）

| 相对路径 | 类型 | 行数 | 角色 | 说明 |
|---|---|---:|---|---|
| `logs/session-20260813-068bbd7d.md` | 文档 | 53 | — | — |
| `logs/session-20260817-4c263012.md` | 文档 | 53 | — | — |

### _resume_audit/

断点续训一致性核验：比较 selected.pt/inflight.pt 检查点并驱动重跑场景（一次性审计）。

文件数：5（.py 1 个，其他 4 个）

| 相对路径 | 类型 | 行数 | 角色 | 说明 |
|---|---|---:|---|---|
| `cmp_ckpt.py` | Python | 86 | 训练入口 | 逐位比较两个检查点（selected.pt 或 inflight.pt）。 |
| `drive_all.sh` | Shell 脚本 | 8 | 驱动脚本 | — |
| `run_case.sh` | Shell 脚本 | 48 | 驱动脚本 | 断点续训审计（单格）：A 连续跑一 / A2 连续跑二 / B 中断恢复跑 |
| `run_full4.sh` | Shell 脚本 | 75 | 驱动脚本 | 断点续训审计（四格整跑，含阶段闸门与 LSPR24 评价） |
| `run_torn.sh` | Shell 脚本 | 31 | 驱动脚本 | 断裂追加台账（torn append）鲁棒性探针： |

### ch3_final_weights_assets/

第三章定稿模型（协议 A 四格）权重的推理资产与说明（数据物化与视图）。

文件数：2（.py 1 个，其他 1 个）

| 相对路径 | 类型 | 行数 | 角色 | 说明 |
|---|---|---:|---|---|
| `README.md` | 文档 | 92 | — | — |
| `inference.py` | Python | 150 | 训练入口 | 第三章定稿模型（协议 A）四格权重的研究用途逐流推理入口。 |

### dijk2026_replication/

Dijk 2026（SSRN 6597680）复现的数据读取层、只读勘察脚本与运行驱动 shell（数据物化与视图 + 一次性审计 + 远程与运维混合，逐文件角色见下表）。

文件数：15（.py 6 个，其他 9 个）

| 相对路径 | 类型 | 行数 | 角色 | 说明 |
|---|---|---:|---|---|
| `dijk_fields.py` | Python | 154 | 机制实现 | Dijk 2026（SSRN 6597680）附录 A 的 83 个输入字段与协议常量。 |
| `dijk_ingest.py` | Python | 293 | 数据物化与视图 | Dijk 2026 复现的数据读取层。 |
| `probe_columns.py` | Python | 56 | 训练入口 | 只读探查：LSPR24 row group 结构与 External_* 取值基数。 |
| `probe_lspr23_head.py` | Python | 49 | 训练入口 | 只读探查 LSPR23 CSV 前 20 万行，确认 83 字段可解析与取值域（有界读取）。 |
| `push_and_run.sh` | Shell 脚本 | 55 | 远程与运维 | 本机辅助：把 tools/dijk2026_replication 下的文件推送到服务器同名目录，并可选执行远程命令。 |
| `recon_data.sh` | Shell 脚本 | 27 | 一次性审计（勘察/核验类驱动脚本） | 只读勘察 LSPR23/LSPR24 原始数据 |
| `recon_receipts.sh` | Shell 脚本 | 13 | 一次性审计（勘察/核验类驱动脚本） | — |
| `recon_remote.sh` | Shell 脚本 | 39 | 远程与运维 | Dijk 2026 复现前的只读环境勘察脚本 |
| `recon_schema.py` | Python | 47 | 一次性审计 | 只读勘察 LSPR23 CSV 表头与 LSPR24 Parquet 模式，核验 Dijk 83 字段可用性。 |
| `recon_splits.sh` | Shell 脚本 | 12 | 一次性审计（勘察/核验类驱动脚本） | — |
| `replicate_dijk_xgboost.py` | Python | 495 | 训练入口 | Dijk 2026（SSRN 6597680）XGBoost 跨年度结果复现主流程。 |
| `run_probe.sh` | Shell 脚本 | 6 | 驱动脚本 | — |
| `run_probe23.sh` | Shell 脚本 | 6 | 驱动脚本 | — |
| `run_recon_schema.sh` | Shell 脚本 | 6 | 一次性审计（勘察/核验类驱动脚本） | — |
| `run_replication.sh` | Shell 脚本 | 47 | 驱动脚本 | 服务器端单入口：内存准入门禁 → Dijk 2026 XGBoost 跨年度复现全流程。 |

### env/

服务器 venv 激活脚本（远程与运维）。

文件数：1（.py 0 个，其他 1 个）

| 相对路径 | 类型 | 行数 | 角色 | 说明 |
|---|---|---:|---|---|
| `activate.sh` | Shell 脚本 | 23 | 驱动脚本 | — |

### lspr24_g0/

LSPR24 物化管线 Rust crate：canonical 化、字段清单、外部排序、G0 资格门与跨年物化（数据物化与视图）。

文件数：48（.py 0 个，其他 48 个）

| 相对路径 | 类型 | 行数 | 角色 | 说明 |
|---|---|---:|---|---|
| `Cargo.lock` | 依赖锁文件 | 965 | — | — |
| `Cargo.toml` | Cargo 配置 | 23 | — | — |
| `configs/lspr24-development-wide-screen-v1.json` | JSON 配置/模式 | 8 | — | — |
| `configs/lspr24-g0-development-v4.json` | JSON 配置/模式 | 11 | — | — |
| `schemas/g0-config-v3.schema.json` | JSON 配置/模式 | 58 | — | — |
| `schemas/g0-receipt-v3.schema.json` | JSON 配置/模式 | 116 | — | — |
| `src/bin/lspr24_development_wide.rs` | Rust 源码 | 31 | 数据物化与视图 | LSPR24 开发宽表单次物化入口。 |
| `src/bin/lspr24_g0_gate.rs` | Rust 源码 | 84 | 数据物化与视图 | LSPR24 G0-A 收据结构与依赖归约入口。 |
| `src/bin/lspr24_g0_materialize.rs` | Rust 源码 | 62 | 数据物化与视图 | LSPR24 G0-D 真实 Parquet 两阶段开发物化命令。 |
| `src/bin/lspr24_schema_audit.rs` | Rust 源码 | 97 | 数据物化与视图 | LSPR24 冻结模式审计与双清单冻结入口。 |
| `src/bin/lspr_crossyear_materialize.rs` | Rust 源码 | 46 | 数据物化与视图 | LSPR23 到 LSPR24 跨年度开发数据物化入口。 |
| `src/canonical.rs` | Rust 源码 | 212 | 数据物化与视图 | 合同冻结的规范元组编码与语义 SHA-256。 |
| `src/config.rs` | Rust 源码 | 32 | 数据物化与视图 | 时间列扫描的资源配置。 |
| `src/development_router.rs` | Rust 源码 | 387 | 数据物化与视图 | 仅面向前 80% 开发选择的标签路由。 |
| `src/external_sort.rs` | Rust 源码 | 408 | 数据物化与视图 | 有界排序段与确定性多路归并。 |
| `src/field_manifest/build.rs` | Rust 源码 | 158 | 数据物化与视图 | 规则表展开、源列类型回填与禁入断言。 |
| `src/field_manifest/json.rs` | Rust 源码 | 92 | 数据物化与视图 | 字段清单的确定性 JSON 文档与排他发布。 |
| `src/field_manifest/mod.rs` | Rust 源码 | 332 | 数据物化与视图 | 合同 §6.1 字段清单：规则表驱动的输出列冻结与禁入断言。 |
| `src/field_manifest/rules.rs` | Rust 源码 | 484 | 数据物化与视图 | 字段清单的唯一事实源：实施计划任务 1 的聚合规则表逐行展开。 |
| `src/formal_parquet.rs` | Rust 源码 | 1005 | 数据物化与视图 | 真实 Parquet 的 G0-D 无标签切分与受限开发物化入口。 |
| `src/gates.rs` | Rust 源码 | 197 | 数据物化与视图 | G0-A 收据完整性、依赖与总状态归约。 |
| `src/input.rs` | Rust 源码 | 80 | 数据物化与视图 | 输入时间列名称与模式校验。 |
| `src/lib.rs` | Rust 源码 | 78 | 数据物化与视图 | LSPR24 G0-D 的确定性开发数据物化库。 |
| `src/lspr_crossyear.rs` | Rust 源码 | 3143 | 数据物化与视图 | LSPR23 到 LSPR24 的流级跨年度开发数据物化。 |
| `src/materialize.rs` | Rust 源码 | 252 | 数据物化与视图 | 前 80% 开发区确定性物化与开发阶段门禁状态。 |
| `src/output.rs` | Rust 源码 | 236 | 数据物化与视图 | 不覆盖正式路径和同目录暂存路径的输出发布。 |
| `src/parquet_scan.rs` | Rust 源码 | 289 | 数据物化与视图 | Parquet 时间列的顺序流式扫描。 |
| `src/receipt.rs` | Rust 源码 | 532 | 数据物化与视图 | 严格的 G0-A 配置与机器收据合同。 |
| `src/schema_audit.rs` | Rust 源码 | 595 | 数据物化与视图 | LSPR24 冻结模式的页脚级审计与去重内容投影清单。 |
| `src/screen/config.rs` | Rust 源码 | 132 | 数据物化与视图 | — |
| `src/screen/history.rs` | Rust 源码 | 43 | 数据物化与视图 | — |
| `src/screen/mod.rs` | Rust 源码 | 20 | 数据物化与视图 | LSPR24 原始行的模式归一化。 |
| `src/screen/output.rs` | Rust 源码 | 361 | 数据物化与视图 | — |
| `src/screen/source.rs` | Rust 源码 | 225 | 数据物化与视图 | — |
| `src/screen/wide.rs` | Rust 源码 | 1334 | 数据物化与视图 | — |
| `src/types.rs` | Rust 源码 | 169 | 数据物化与视图 | 稳定排序所需的新类型与记录类型。 |
| `tests/canonical_hash.rs` | Rust 源码 | 101 | 数据物化与视图 | — |
| `tests/common/mod.rs` | Rust 源码 | 28 | 数据物化与视图 | 两个合同测试共享的冻结模式夹具装载。 |
| `tests/contract_binding_v5.rs` | Rust 源码 | 129 | 数据物化与视图 | 合同 v5 绑定回归测试。 |
| `tests/development_router_contract.rs` | Rust 源码 | 100 | 数据物化与视图 | — |
| `tests/field_manifest_contract.rs` | Rust 源码 | 280 | 数据物化与视图 | 任务 1 合同测试：字段清单规则表展开、禁入断言与 JSON 冻结形状。 |
| `tests/fixtures/lspr24-v2-schema-audit.json` | JSON 配置/模式 | 616 | — | — |
| `tests/formal_development_entry_contract.rs` | Rust 源码 | 253 | 数据物化与视图 | — |
| `tests/materialize_contract.rs` | Rust 源码 | 188 | 数据物化与视图 | — |
| `tests/parquet_time_scan.rs` | Rust 源码 | 174 | 数据物化与视图 | — |
| `tests/receipt_contract.rs` | Rust 源码 | 213 | 数据物化与视图 | — |
| `tests/schema_audit_contract.rs` | Rust 源码 | 219 | 数据物化与视图 | 任务 1 合同测试：页脚级模式审计、schema_sha256 金标准与去重投影清单。 |
| `tests/stable_external_sort.rs` | Rust 源码 | 145 | 数据物化与视图 | — |

### r2_genis_totbytes_verifier/

pcap 总字节数校验 Rust crate（一次性审计）。

文件数：12（.py 0 个，其他 12 个）

| 相对路径 | 类型 | 行数 | 角色 | 说明 |
|---|---|---:|---|---|
| `Cargo.lock` | 依赖锁文件 | 1310 | — | — |
| `Cargo.toml` | Cargo 配置 | 31 | — | — |
| `README.md` | 文档 | 121 | — | — |
| `src/archive.rs` | Rust 源码 | 144 | 一次性审计 | — |
| `src/cli.rs` | Rust 源码 | 72 | 一次性审计 | — |
| `src/flow.rs` | Rust 源码 | 1702 | 一次性审计 | — |
| `src/lib.rs` | Rust 源码 | 18 | 一次性审计 | — |
| `src/main.rs` | Rust 源码 | 10 | 一次性审计 | — |
| `src/model.rs` | Rust 源码 | 182 | 一次性审计 | — |
| `src/output.rs` | Rust 源码 | 220 | 一次性审计 | — |
| `src/packet.rs` | Rust 源码 | 447 | 一次性审计 | — |
| `src/pcapng.rs` | Rust 源码 | 318 | 一次性审计 | — |

### r2_quic_qlog_audit/

QUIC qlog 审计 Rust crate（一次性审计）。

文件数：3（.py 0 个，其他 3 个）

| 相对路径 | 类型 | 行数 | 角色 | 说明 |
|---|---|---:|---|---|
| `Cargo.lock` | 依赖锁文件 | 348 | — | — |
| `Cargo.toml` | Cargo 配置 | 23 | — | — |
| `src/main.rs` | Rust 源码 | 1629 | 一次性审计 | — |

### remote_exec/

GPU 服务器环境探测与 rsync 推拉 expect 脚本（远程与运维）。

文件数：3（.py 0 个，其他 3 个）

| 相对路径 | 类型 | 行数 | 角色 | 说明 |
|---|---|---:|---|---|
| `gpu_env_quiet.exp` | expect 脚本 | 71 | 远程与运维 | — |
| `gpu_rsync_pull.exp` | expect 脚本 | 33 | 远程与运维 | 从服务器拉取制品到本机（与 gpu_rsync_push.exp 对称，方向相反）。 |
| `gpu_rsync_push.exp` | expect 脚本 | 54 | 远程与运维 | — |
