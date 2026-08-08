# GeNIS 候选协议双构建制品独立复审

- **复审日期**：2026-07-28
- **复审对象**：
  - `/root/autodl-tmp/thesis/experiments/llm_probe/runs/data-candidate-builds/genis-v0/build-a`
  - `/root/autodl-tmp/thesis/experiments/llm_probe/runs/data-candidate-builds/genis-v0/build-b`
- **复审方式**：服务器只读检查；未修改、移动或发布任何服务器文件。
- **依据**：[实现报告](implementation-report.md)与[统一数据冻结与 PINN 候选顺序实验合同](../../2026-07-24-统一数据冻结与PINN候选顺序实验合同.md)。

## 1. 结论

**严重问题 0 项，重要问题 0 项，建议 2 项。**

两份构建的文件集合与逐文件内容一致，未保留 `_INCOMPLETE` 标记；冻结协议加载器分别通过；主表行数、主键、标签、分区、分组隔离、精确重复排除、未知子类隔离和七份清单成员关系均与实现合同一致。

**允许主进程把其中一份构建原子发布到 `runs/data-frozen/dataset-candidate-genis-v0/protocol/`，但发布对象只能标记为 `provisional`、`theory_selection` 的 GeNIS 候选组件。** 它不是三源合并后的完整 `dataset-v1`，不得用于最终调参、读取最终测试结果后选路或形成论文最终测试结论。

## 2. 问题分级

### 2.1 严重问题

无。

### 2.2 重要问题

无。

### 2.3 建议

1. 构建内的 `protocol.yaml` 仍为 `review_status: review_pending`，`audit/p0-subset.json` 仍为 `reproducibility.status: pending_external_rerun` 且 `formal_protocol_gate_complete: false`。这是实现合同预设的候选阶段状态，不阻塞本次候选目录发布。发布记录应在制品外绑定本复审报告和确定性审计哈希，不要为了改状态而原地编辑已验证构建，否则会破坏双构建逐字节一致证据。
2. 本次复核重新计算了构建直接消费的六个派生 JSONL、会话分配、划分摘要、物化摘要和候选构建代码哈希；上游原始 CSV 只核对了候选内保存的血缘声明，未在本次复审中再次读取并计算全部原始 CSV。完整 `dataset-v1` 冻结时仍应按统一合同重新生成原始来源校验清单。

## 3. 文件完整性与确定性

### 3.1 文件集合

- `build-a`：20 个文件。
- `build-b`：20 个文件。
- 两边按相对路径排序后的文件集合摘要均为 `1a2cc6ee92fb03d7a1e47c5db368e9194afce9fecd68612aaa0c67af813bfe49`。
- 两边均不存在 `_INCOMPLETE`。
- 每份构建约 626 MiB；两边 `samples.parquet` 均为 234,006,379 字节。

20 个文件包括主表、协议、字段角色、标签合同、来源血缘、候选清单、6 个审计文件和 7 个划分清单，没有发现缺失或额外文件。

### 3.2 逐文件哈希

- 两边分别执行 `sha256sum -c audit/artifact-sha256.txt`，清单登记的 18 个文件全部返回 `OK`。
- 两边 `audit/artifact-sha256.txt` 的 SHA-256 均为 `a454c09c80ccde146995496ac44bb2842cdb570f7f292a882e492123ce2c6a1b`。
- 两边 `protocol.yaml` 的 SHA-256 均为 `ec2c81f404da48edae5c518cdd8ce8269cb979e73cc506a42c8933b63b35a9f0`。
- 两边 `samples.parquet` 的 SHA-256 均为 `2b0d8b49ef81db3a9f9338dfbabe185bab54c02512786c9f64f52718ee8c55a0`。

内嵌哈希清单覆盖除自身和最终 `protocol.yaml` 外的全部文件；上述额外交叉哈希补齐了这两个文件，因此两份构建的 20 个文件均已纳入逐字节一致性裁决。

### 3.3 外置确定性审计

服务器已有 `runs/data-candidate-builds/genis-v0/determinism-audit.json`：

- 文件大小：2,398 字节。
- SHA-256：`502054de2bae786b4a63647924c6763258467d9952babfba367e16376fd57940`。
- JSON 结构完整，记录 `byte_identical=true`、`file_count=20`、两边清单数均为 7，并列出全部相对路径哈希。

本复审没有直接采信该声明，而是用文件集合摘要、两边内嵌哈希清单和协议哈希重新交叉验证，结论一致。

## 4. 冻结协议加载验收

对 `build-a` 与 `build-b` 分别调用：

```python
load_frozen_protocol(
    root,
    expected_protocol_version="data-protocol-v1.0-rc1",
    expected_status="provisional",
    expected_phase="theory_selection",
)
```

两边均成功返回：

- 样本数：1,372,690。
- 协议 SHA-256：`ec2c81f404da48edae5c518cdd8ce8269cb979e73cc506a42c8933b63b35a9f0`。
- 主表 SHA-256：`2b0d8b49ef81db3a9f9338dfbabe185bab54c02512786c9f64f52718ee8c55a0`。
- 协议状态：`provisional`。
- 协议阶段：`theory_selection`。
- 清单数：7。

协议同时明确：`final_tuning_allowed=false`、`final_test_claim_allowed=false`、`test_and_open_set_used_for_route_selection=false`，与候选阶段合同一致。

## 5. 主表独立复算

### 5.1 主键与记录

- 总行数：1,372,690。
- 唯一 `sample_id`：1,372,690。
- 重复 `sample_id`：0。
- 不符合 `genis:[0-9a-f]{64}` 的 `sample_id`：0。
- 不符合 64 位小写十六进制的 `candidate_record_sha256`：0。
- 开发可用记录：161,723。
- 因与训练集观测完全重复而排除的验证记录：2,485。

### 5.2 分区与标签

| 分区 | 行数 |
| --- | ---: |
| `train` | 151,324 |
| `validation` | 12,884 |
| `test` | 29,314 |
| `ood:dos-icmp` | 393,216 |
| `ood:dos-pushack` | 392,736 |
| `ood:dos-udp` | 393,216 |

二元标签计数为良性 28,223、恶意 1,344,467；家族标签计数为良性 28,223、暴力破解 18,310、拒绝服务 1,326,157。以上结果与 `candidate-manifest.json` 和 `audit/label-coverage.json` 完全一致。

### 5.3 分组与泄漏

- 全分区唯一 `group_id`：183,704。
- 开发分区唯一 `group_id`：43,801。
- 任一 `group_id` 跨来源分区：0。
- 训练与严格验证的 `observation_sha256` 交集：0。
- 训练集未知子类交集：空。
- 开放集子类：恰为 `dos-icmp`、`dos-pushack`、`dos-udp`。
- 开放集家族：仅为 `dos`。
- 字段预算只把八个公共流级观测及八个缺失掩码列为 `model_input`；标签、分组、分区、来源和哈希均未进入模型输入，敏感字段命中数为 0。

因此，候选制品支持“未知子类而非未知家族”的准确表述，不能把该开放集写成未知攻击家族检测。

## 6. 七份清单核验

| 清单 | 行数 | 重复主键 | 与主表语义分区的对称差 |
| --- | ---: | ---: | ---: |
| 家族开发训练 | 151,324 | 0 | 0 |
| 家族开发验证 | 10,399 | 0 | 0 |
| 家族时间前向测试 | 29,314 | 0 | 0 |
| 子类开发训练 | 151,324 | 0 | 0 |
| 子类开发验证 | 10,399 | 0 | 0 |
| 子类开放集测试 | 1,179,168 | 0 | 0 |
| 子类时间前向测试 | 29,314 | 0 | 0 |

同一开发训练、开发验证和时间前向测试内，家族任务与子类任务的 `sample_id` 序列分别完全相同。冻结加载器还验证了清单哈希、样本存在性和同一任务套件内的跨划分冲突，均通过。

## 7. 输入血缘复核

重新计算后，以下当前服务器输入与候选血缘记录一致：

- 六个派生分区 JSONL：`train`、`validation`、`test`、`ood_dos-icmp`、`ood_dos-pushack`、`ood_dos-udp`。
- `session_assignments.jsonl`：`d4d3909abab9900f5c38bc5d3799991b52d3dc1eceb9d79ff02026e128eb4cae`。
- `plan_summary.json`：`6ed8ee35f95c5cba9d6b162aef8a3a9c2e04aae72bc18e72f981bdccaa7f8042`。
- `materialization_summary.json`：`1aef385f8e203bd55f62c71daddb11bb4aee8591a8b1ff007334192dc006e19a`。
- `src/flow_probe/genis_candidate.py`：`d0eca7d0b41bafb7976ee6fa78cf43e4db51220dc312b1495cd5d729345036ae`。

候选内记录 `absolute_paths_persisted=false`，来源路径均为相对血缘路径。

## 8. 发布裁决与边界

主进程可以执行原子发布，但必须同时满足：

1. 目标目录尚不存在，禁止覆盖旧版本。
2. 发布只采用已经复审的一份完整构建，且发布前再次核对 `protocol.yaml` 和 `samples.parquet` 的上述 SHA-256。
3. 外置保存本复审报告和 `determinism-audit.json` 的哈希，保留另一份构建直到发布回收记录完成。
4. 发布后的用途仍限制为 GeNIS `theory_selection` 候选组件；不得把 `review_pending` 改写成完整三源数据冻结已经完成。
5. 后续只有在 GeNIS、TQH-C2 与 ns-3 合并、全部协议清单与泄漏审计通过后，才能签发完整 `dataset-v1`。

本复审未执行发布操作，也未修改任何服务器制品。
