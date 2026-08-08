# TQH-C2 A/B/C 固定预算物化路径独立复审

## 结论

**不通过，暂时禁止启动真实双物化。**

- 严重问题：0 项。
- 重要问题：1 项。
- 一般问题：1 项。
- 已知服务器验证：精确测试 16/16 通过，Black、语法检查与 Ruff 通过。本审查按约束未运行本地 `pytest`。

## 审查发现

### 重要：实际固定清单不满足生产代码要求的域内验证集三档 jitter 覆盖

计划明确要求域内验证集和测试集都覆盖 A/B/C、四档 interval 与三档 jitter。生产校验器也在 `src/flow_probe/tqh_c2_candidate_abc_fixed.py:164` 至 `src/flow_probe/tqh_c2_candidate_abc_fixed.py:170` 对域内 validation 和 test 同时要求三档 jitter。

但是，实际配置 `configs/tqhc2_abc_fixed_assignment_v1.json` 的四个域内 validation cell 全部属于 `jitter=70`：

- `A_i300_j70`
- `A_i30_j70`
- `B_i3600_j70`
- `C_i1800_j70`

配置自身也在 `configs/tqhc2_abc_fixed_assignment_v1.json:625` 记录 `validation_jitter_count` 为 1。服务器通过的测试没有发现该问题，因为 `tests/test_tqh_c2_candidate_abc_fixed.py:191` 至 `tests/test_tqh_c2_candidate_abc_fixed.py:237` 使用测试内生成的合成清单，没有加载版本库中的真实固定 JSON。

**影响：** 真实物化将在 `load_fixed_suite_groups` 的硬覆盖检查处立即失败，无法生成候选协议；如果为绕过失败而放宽生产校验，则又会违反已冻结的数据合同。因此，在重新生成符合三档 jitter 覆盖的域内分配、更新固定清单哈希并增加真实配置验收测试之前，不能开始双物化。

### 一般：预算合同中的算法标识和源样本总数未被显式核验

`src/flow_probe/tqh_c2_candidate_abc_fixed.py:719` 至 `src/flow_probe/tqh_c2_candidate_abc_fixed.py:732` 只在上限一致时核对预计样本数与包数，没有核对固定清单中的 `sampling_algorithm` 和 `source_mapped_sample_count`。当前实现实际使用硬编码抽样算法，36 个 cell 的逐项绑定也间接约束了源样本总数，因此这不会改变当前数据结果，不列为重要问题；但清单元数据被误改时可能产生审计记录自相矛盾。

## 独立统计

对实际固定清单进行只读复算得到：

- cell 数：36，其中 A/B/C 各 12 个。
- 映射流总数：303,599。
- 原始类别计数：良性 273,359，恶意 30,240。
- 每 cell 上限 1,000 后：35,235 条流。
- 最大余数法复算：良性 27,076，恶意 8,159，总计 35,235。
- 固定清单 SHA-256：`f3af9b362837d617216ab12b224642aa83bbeecadbf0f30750e8349ecff925fc`，与实施报告一致。
- 四套 cell 数分别为 28/4/4 和三个 20/4/12；三个留一 profile 套件的 validation 均覆盖两个源 profile、四档 interval 和三档 jitter，test 均完整覆盖被留出的 12 个 cell。
- 只有域内 validation 的 jitter 覆盖不符合合同；域内 test 覆盖三档 jitter。

## 其余审查结果

- 最大余数法实现使用整数商余数，余数并列时按标签字典序裁决；类内按 `sha256("tqhc2-abc-budget-v1|" + sample_id)` 和 `sample_id` 稳定排序。
- 包表按 profile 和行组扫描，只拼接目标样本；行组内 sample 交错不再被误判为不连续，最终按 `sample_id, packet_index` 稳定恢复。
- 目标样本执行包序号重复、缺口、回退、主记录计数、profile/cell 绑定和有限数值校验；聚合及序列摘要复用既有实现。
- 每个 profile 完成后释放包级中间表，不同时保留三个 profile 的目标包表。
- 输出目录拒绝覆盖，失败时保留 `_INCOMPLETE`；成功协议保持 `review_pending`，并禁止最终调参与测试结论。
- 未发现模型预测或最终测试性能参与固定分配与样本抽取，也未发现模型字段包含标签字段的直接数据泄漏路径。

## 修复与复审要求

1. 只重新执行一次 36-cell 层面的固定分配生成，使域内 validation 同时覆盖 A/B/C、四档 interval 和三档 jitter；不得使用模型输出或测试性能。
2. 更新固定清单及其 SHA-256，并增加一项直接加载版本库真实配置的服务器精确测试，避免合成夹具再次掩盖配置错误。
3. 仅重跑固定分配加载相关的最小服务器测试；通过后重新进行独立复审。
4. 严重和重要问题归零后，再串行启动两次真实预算物化。

## 残余风险

即使修复上述阻塞，真实包表的 2,475,729 条目标包计数、峰值常驻内存、运行时长和两份输出逐字节一致性仍未在真实物化中验证。这些属于任务 4 的运行门禁，不能由小型测试替代。
