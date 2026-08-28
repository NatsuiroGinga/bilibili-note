# N-16 独立审查修复计划

- **日期**：2026-08-22
- **路线**：`RESEARCH_ROUTE=RWKV`，第三章 N-16
- **实现代理**：`n16_review_fix_impl_sol_high`，模型 `gpt-5.6-sol`，`effort=high`
- **基线提交**：实施计划 `fe00c71`、补充审计 `b2800d2`、原实现 `a7451d5`
- **当前状态**：修复进行中；SwanLab 部分等待统一追踪接口提交，未达到 `READY`

## 一、边界

只修改以下五个既有文件：

1. `thesis/experiments/llm_probe/tools/ch3_common_first_alert_fp_budget_envelope.py`
2. `thesis/experiments/llm_probe/configs/ch3-common-first-alert-fp-budget-envelope-v1.json`
3. `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_common_first_alert_fp_budget_envelope_v1.sh`
4. `.Codex/docs/RWKV/2026-08-21-共同实际首次告警FP预算包络实施报告.md`
5. 本目录的 `task_plan.md` 与 `notes.md`

不访问服务器，不运行实验，不修改既有评分辅助脚本，不修改统一追踪实现，不覆盖、回滚、暂存或提交其他代理与用户的改动。

## 二、修复任务

| 优先级 | 状态 | 动作 | 验收证据 |
| --- | --- | --- | --- |
| P0 | 待处理 | 将 XGBoost 与 MLP 的 `probability_clip` 冻结为 `null`，删除实际裁剪路径 | 配置门、方法收据与构造真值检查均证明原始有限 `[0,1]` 概率直接进入公式 |
| P0 | 待处理 | 在配置中冻结两个实际评分辅助脚本 SHA-256，导入前核验，并纳入输入门、方法身份、分数来源收据和最终清单 | 任一脚本变化均拒绝重放或恢复 |
| P0 | 待处理 | 去除额外 `float64[N]`、`int64[N]` 候选和每预算全流临时数组，改为按实体或固定块扫描 | 配置只保留计划允许的全流数组；实施报告完整列出共享构造与方法阶段瞬时峰值 |
| P0 | 待处理 | 恢复时重新扫描禁止制品和额外制品，当前允许文件集合与清单严格相等；SwanLab 原始日志逐文件纳入 | 增删任一未登记文件或出现禁止文件均拒绝恢复成功 |
| P0 | 待处理 | 只把模型身份或重放不可达登记为方法级 `unreachable`，其他工程、代码、依赖与资源异常仍使整次运行失败 | 其余可达方法描述性曲线保留，不形成五方法裁决 |
| P0 | 待处理 | 冻结状态枚举，区分流程完成与五方法包络闭合；启动器读取 `manifest.complete` | `complete=false` 不得输出 `ALREADY_COMPLETE` |
| P1 | 待处理 | 分数来源收据补原始概率范围、在线公式、`probability_clip=null` 和 XGBoost `p=1` | 五方法收据字段完整且机械校验 |
| P0 | 阻塞 | 导入统一 SwanLab 标签门与发布接口，不自建重复门 | 等待 `swanlab_tag_gate_impl_sol_high` 的提交后再接入并验证标签不超过 20 个 |
| P0 | 待处理 | 保留已审查通过的核心公式 | 完整同分组、整数 FP 最后可达点、终端与路径分离、六档 1 基及时曲线构造真值继续通过 |

## 三、实施顺序

1. 读取 N-16 四个实现文件、冻结计划与独立审查完整 findings。
2. 先修配置、输入身份与概率语义，再重写有界扫描和恢复校验。
3. 接入统一追踪接口；若上游尚未提交，只记录阻塞，不提交生产修复。
4. 更新实施报告，明确瞬时峰值、状态语义、不可达边界和未运行事实。
5. 执行允许的静态验证与计划允许的构造真值内存检查。
6. 仅暂存本任务拥有文件，提交生产修复并回报剩余阻塞。

## 四、允许的验证

- `python -m py_compile`
- 模块导入
- `--help`
- `--validate-config`
- `bash -n`
- 限定文件 `git diff --check`
- 计划允许、具有明确构造真值的公式与内存形状检查

禁止运行 `black`、自动格式化器、人工夹具、单元测试、集成测试、服务器命令或真实实验。

## 五、完成门

只有八项审查问题全部关闭、统一 SwanLab 接口已接入、允许验证全部通过且生产修复独立提交后，才可标记 `READY`。真实数据和科学结果仍为实验待证。
