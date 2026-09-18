# SDD ledger — plan: .Codex/docs/RWKV/2026-09-03-C10缩容档配置补齐实施计划.md

## 预检扫描（任务 1 派发前）

| 检查项 | 内容 | 结果 |
| --- | --- | --- |
| 任务 1 ↔ 任务 2 共享 | 任务 1 产出 configs/ch3-ft-c10-halfwidth-screening-v1.json；任务 2 消费同一路径跑 --validate-config | 一致，无冲突 |
| 任务 2 ↔ 任务 3 共享 | 任务 2 产出 science_identity_sha256；任务 3 推送前核对 | 一致 |
| 任务 3 ↔ 任务 4 共享 | 任务 3 产出运行目录 runs/diagnostics/ch3-ft-c10-halfwidth-screening-v1/；任务 4 读其 checkpoints/inflight.pt | 一致 |
| 任务 1 自洽 | 步骤 1 生成的键 vs 步骤 2 断言的键 | 九项断言全部对应步骤 1 写入的字段，自洽 |
| 任务 2 自洽 | 步骤 1 核验新配置 vs 步骤 2 核验既有三份不变 | 自洽 |
| 任务 4 自洽 | 依赖「ETA 在 z2=0 不进训练图」，该前提由 C11 配置 scope 字段原文支撑 | 自洽；前提若假，任务 4 步骤 2 即为报告出口 |
| 全局约束 vs 任务 | Global Constraints 的白名单四键、alpha=0.5、不改宿主 .py | 任务 1 步骤 1 只写配置，未触宿主；一致 |
| 规则冲突 | 仓库禁止创建人工夹具/单元测试；计划各步骤用的是内联断言与宿主 --validate-config，非 pytest 夹具 | 无冲突 |

扫描结论：无需裁决的冲突。

BASE = e0735b0
