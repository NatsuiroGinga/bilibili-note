# 强基线运营指标总表接入计划

## 目标

将 XGBoost＋CPA-ELP C11 与已发表 Transformer/CNN/GRU 的目标年完整实际可达曲线和同轴首次告警制品接入第三章统一总表，同时保留旧来源中的 LSPR23 选择、源年性能、训练资源和模型身份。禁止因目标年回填没有源年分数而删除、伪造或替换源年证据。

## 输入制品

1. `runs/diagnostics/ch3-xgb-cpa-elp-c11-operational-backfill-v1-rerun2`
   - `finished/complete/exit0`
   - 目标打分一次、未重训、未持久化逐流/逐实体分数
2. `runs/diagnostics/ch3-published-neural-operational-backfill-v1`
   - `finished/complete/exit0`
   - Transformer/CNN/GRU 三模型独立结果，不融合分数
   - 训练、推理和 GPU 数组读取均为 0

两运行的本地回收文件已经按各自 manifest 全部通过字节数和 SHA-256 核验。

## 设计裁决

### 目标年运营覆盖层

保持来源配置每行原有 `source_schema`、`relative_path`、`config_type`、训练预算、选择协议和资源适配器不变，新增可选 `target_operational_overlay`：

- `schema`：区分 XGBoost 单单元回填和三模型共享回填。
- `relative_path`：聚合结果。
- `model_key` 或 `cell`：选择共享运行中的独立模型或 C11。
- 完整预算曲线收据与 NPZ 路径。
- 首次告警收据与 NPZ 路径。
- `manifest`、完成状态和资源收据路径。

生成器先调用既有适配器形成原始行，再把覆盖层只应用到 LSPR24 目标年字段：

1. 用回填制品的全精度逐流 AP、实体 AP、最大池化实体 AP替换对应目标年旧标量。
2. 用完整并列组阶梯曲线按 `actual_fpr <= nominal_fpr` 重算六档 DR。
3. 接入 1 基 `exposure_index` 首次告警未告警率、实际首次告警 FPR 和按时检出曲线。
4. 保留旧源年选择、源年性能和模型训练资源；后处理资源只进溯源和专用字段，不覆盖模型训练/推理资源。
5. 覆盖层状态或哈希不完整时整行保持旧结果并标 `pending_reason`，不得部分静默覆盖。

### 年度与证据边界

- 新回填只有 LSPR24 完整曲线，LSPR23 完整曲线和首次告警继续缺失。
- `lspr23-performance` 中相关行必须继续标证据不完整，不得从目标年制品反推源年。
- `lspr24-evaluation` 可使用新实际曲线和同轴首次告警参与当前目标年性能前沿。
- XGBoost 树数不折算神经参数量；已发表神经后处理资源不替换其历史训练时间。
- 4% 只作名义预算键，表中必须同时保存实际可达 FPR；不得用旧名义标量覆盖完整曲线读数。

## 文件所有权

实现代理只修改：

1. `thesis/experiments/llm_probe/tools/ch3_build_metrics_table.py`
2. `thesis/experiments/llm_probe/configs/ch3-metrics-table-sources-v1.json`
3. `.Codex/docs/RWKV/2026-08-20-第三章全模型指标总表/` 下现有 13 个生成文件
4. `.Codex/docs/RWKV/2026-08-21-强基线运营指标总表接入/实施报告.md`

不得修改回填运行、训练工具、恢复卡、正文或其他模型行的来源身份。

## 必需适配

- XGBoost 旧行附加 C11 回填覆盖层。
- CNN、GRU、Transformer 三行附加共享神经回填中的各自 `model_key`。
- 覆盖层读取独立 manifest/status/resource，并将所有输入加入 `provenance.json`。
- 完整曲线和首次告警轴只接受统一合同允许的 `exposure_index`；`time_delay_available=false`。
- 同一模型的覆盖结果必须复现旧逐流 AP、实体 AP 和历史 DR@4% 锚，否则生成失败。

## 验收

1. Python 语法、导入、`--help`、配置验证。
2. 使用真实回收制品重建全部 13 个输出文件。
3. 行数与模型身份不变，不新增重复模型行。
4. 四条目标年行均读取实际六档 DR、完整曲线和首次告警。
5. 四条源年行不伪造缺失的完整曲线或首次告警。
6. `provenance.json` 包含覆盖层主结果、两份 NPZ/收据、manifest/status/resource 的 SHA-256。
7. 其他模型旧锚点逐位不变。
8. `git diff --check` 通过。

不运行 `black`、人工夹具、单元测试或服务器实验；真实总表重建是本任务的主要验证。

## 状态

- [x] 输入制品完成并通过 manifest 核验。
- [x] 冻结目标年覆盖层设计。
- [ ] 实现生成器和配置覆盖层。
- [ ] 真实重建、检查并提交。

