# TQH-C2 A/B/C 预算双物化验证报告

- **验证日期**：2026-07-29
- **验证范围**：只读核验两份独立物化制品，不发布协议，不修改生产代码，不运行本机 `pytest`，不提交 Git。
- **运行状态**：`双物化=全部完成`
- **总体结论**：通过。两次物化的文件集合及全部文件内容完全一致，计数、清单、未完成标记和候选协议加载门禁全部通过。

## 1. 输入与输出

固定输入摘要：

| 输入 | SHA-256 |
| --- | --- |
| `configs/tqhc2_abc_fixed_assignment_v1.json` | `4a274a0449147d4ef6f478471acf3514c4a3b474806e88403c7c7bf09e8274f7` |
| `src/flow_probe/tqh_c2_candidate_abc_fixed.py` | `12fc0fcc21eee068fae57d96a30dee88f8a162c2567781953d35db763073a589` |
| `runs/data-freeze-configs/tqhc2-abc-v0/approved-inputs.json` | `191f737ae18eec982b8031b1ced2e6f74b3f122e6c1fa0bc97596ab3cdada610` |

输出目录：

- 第一次：`/tmp/tqh-candidate-abc-budget-v1-run1-20260728/protocol`
- 第二次：`/tmp/tqh-candidate-abc-budget-v1-run2-20260728/protocol`
- 持久化运行记录：`thesis/experiments/llm_probe/runs/data-materialization/tqhc2-abc-budget-v1-20260728/`

## 2. 运行资源

| 运行 | 实际耗时 | 用户态耗时 | 系统态耗时 | 最大常驻内存 |
| --- | ---: | ---: | ---: | ---: |
| 第一次 | 608.41 秒 | 449.70 秒 | 15.11 秒 | 951,812,096 字节 |
| 第二次 | 484.44 秒 | 428.65 秒 | 11.09 秒 | 954,826,752 字节 |

两次运行各约 8 至 10 分钟，并在本机完成。第二次结束时无需再中断任务或迁移服务器。

## 3. 双份一致性

| 检查项 | 第一次 | 第二次 | 结果 |
| --- | ---: | ---: | --- |
| 文件总数 | 26 | 26 | 通过 |
| 文件集合 | 26 个相同相对路径 | 26 个相同相对路径 | 通过 |
| 逐文件 SHA-256 不一致数 | 0 | 0 | 通过 |
| 全部文件逐字节一致 | 是 | 是 | 通过 |
| `protocol.yaml` SHA-256 | `1c001a0a0808f8a7403b31dabad6a10faf249cf5b9870e618de745b5ed4c1d60` | 相同 | 通过 |
| `samples.parquet` SHA-256 | `05cb0774f8197f07d842a21d3c22ce07c111289b7cabe6950023b689c6b51dac` | 相同 | 通过 |

## 4. 数据与协议门禁

| 检查项 | 第一次 | 第二次 | 结果 |
| --- | ---: | ---: | --- |
| `samples.parquet` 行数 | 35,235 | 35,235 | 通过 |
| `sample_id` 全局唯一 | 是 | 是 | 通过 |
| 样本表 `packet_count_kept` 求和 | 2,475,729 | 2,475,729 | 通过 |
| 预算审计包总计 | 2,475,729 | 2,475,729 | 通过 |
| 三个 profile 包过滤审计求和 | 2,475,729 | 2,475,729 | 通过 |
| 流式审计保留包总计 | 2,475,729 | 2,475,729 | 通过 |
| 划分清单数量 | 12 | 12 | 通过 |
| `_INCOMPLETE` | 不存在 | 不存在 | 通过 |
| `FrozenProtocol` 加载 | 成功 | 成功 | 通过 |

候选协议加载时显式使用以下合同：

- `expected_protocol_version="data-protocol-v1.0-rc1"`
- `expected_status="provisional"`
- `expected_phase="theory_selection"`

两份协议均完成制品摘要、字段角色、样本表、12 份清单及套件内划分互斥验证。

## 5. 验证过程说明

第一次只读加载调用沿用了 `FrozenProtocol` 的正式协议默认版本 `data-protocol-v1.0`，因此被候选协议版本 `data-protocol-v1.0-rc1` 正确拒绝。错误信息直接指明版本差异。核对 `protocol.yaml` 后，按候选协议合同显式传入版本、状态和阶段，最小复核一次即通过。该问题属于验收命令参数错误，不是物化制品或生产代码错误；未修改任何代码或数据。

## 6. 裁决边界

- 双物化复现门禁已经通过，可以由主代理进入原子发布前的最终裁决。
- 本报告不执行发布，因此当前制品仍为 `provisional`、`review_pending`。
- 本报告不证明最终测试结果，也不允许使用测试 cell 或留一 profile 测试域进行调参或归一化统计。
- 未修改生产代码、测试、配置、两份恢复文档或运行制品。
