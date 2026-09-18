# DRIFT 双侧风险约束更新专家混合折0短步实施报告

## 状态

- 实现状态：静态实现与入口验证已完成；真实数据运行尚未启动。
- 科学状态：实验待证。只有同一身份的折0三臂真实运行才可输出 `eligible_for_formalization_only` 或 `rejected_after_finite_step`。
- 范围：只读取并核验现有 G2 折0端点、两个 Adam 状态、冻结探针、两份梯度、14 份 arm 收据和同一固定 32 x 1024 成员块；不读取折1或 T18--T25，不重训 N12。

## 技能与读取收据

- 读取时刻（UTC）：`2026-09-08T09:23:20Z`。
- `/Users/bilibili/.codex/plugins/cache/claude-plugins-official/superpowers/6.3.0/skills/subagent-driven-development/SKILL.md`：SHA-256 `8dd1b8e698edec3700c6d89517dbe96febd3bacd3f6ea21c1a3569c62ea104b5`。
- `/Users/bilibili/.codex/skills/backup/daily-coding-20260811-112930/SKILL.md`：SHA-256 `da2399b50859b9d57281b9bc0dc456082db93d47486ae22967ebf3f17d354ae3`。
- `/Users/bilibili/.codex/skills/pytorch-patterns/SKILL.md`：SHA-256 `22b76f559f17d4b0e44eda71d353065e5da181203d165546edb08c16cc362d85`。
- 冻结研究卡：[第三章-DRIFT双侧风险约束更新专家混合研究卡.md](/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/methods/第三章-DRIFT双侧风险约束更新专家混合研究卡.md)。
- 冻结实施计划：[implementation-plan.md](/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/.Codex/docs/2026-09-08-DRIFT更新专家混合/implementation-plan.md)。

## 已实现

- [ch3_drift_update_expert_mixture_fold0_short_step.py](/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe/tools/ch3_drift_update_expert_mixture_fold0_short_step.py)：核验 G2 折0身份、两个梯度、14 份既有 arm 收据与成员块；从梯度矩阵枚举单纯形顶点重算全局 LP、最小最大违约和每分支不可行诊断，并发布 `solver-receipt.json`。
- [ch3-drift-update-expert-mixture-fold0-short-step-v1.json](/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe/configs/ch3-drift-update-expert-mixture-fold0-short-step-v1.json)：冻结三臂、总质量6、执行系数、G2 输入哈希和 LP 原始内积收据。
- [run_ch3_drift_update_expert_mixture_fold0_short_step_v1.sh](/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_drift_update_expert_mixture_fold0_short_step_v1.sh)：在统一 `launch_run_with_pull.sh` 前显式同步并哈希核验新工具、配置与启动器。
- 更新臂每批独立反向并分别调用两支优化器的 `step()`；仅共享编码器参数可更新，辅助头与探针冻结。评价只用冻结探针，完整保存三个 BCE、AP、AUROC、默认与源侧阈值指标、Brier、ECE、模型/优化器哈希、更新范数和 32 批计数。
- 有限步解释明确写入结果：Adam 预条件、裁剪和非线性使运行成为对 raw-gradient LP 的真实检验，不保证保持线性可行性。

## 静态验证

- 通过：`/opt/miniconda3/envs/rwkv/bin/python -m py_compile tools/ch3_drift_update_expert_mixture_fold0_short_step.py`。
- 通过：`/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_update_expert_mixture_fold0_short_step.py --help`。
- 通过：模块导入并输出 `ch3-drift-update-expert-mixture-fold0-short-step-v1`。
- 通过：`jq empty configs/ch3-drift-update-expert-mixture-fold0-short-step-v1.json`。
- 通过：`bash -n scripts/remote_launchers/run_ch3_drift_update_expert_mixture_fold0_short_step_v1.sh`。
- 通过：计划范围内 `git diff --check`。

## 2026-09-08 真实运行修复

- 根因：真实入口已完成全局 3 x 6 矩阵构造，但随后将每个分支的 3 x 3 披露诊断复用给只接受 3 x 6 的顶点枚举器，导致在短步前抛出维度错误。
- 修复：`solve_max_min_simplex` 现在接受每行等长且 `N >= 1` 的 3 x N 矩阵；全局 3 x 6 的权重、最大最小裕量和三项残差仍按冻结值严格核验。
- 边界：字符、子词各自的 3 x 3 gamma 只写入 `solver-receipt.json` 的披露诊断，不再逐项与配置中的单一全局参考数比较，也不参与任何新增门禁或裁决。

## 当前文件哈希

- 工具：`a275e564e94092bff483946f9d2f3cf7512f470acdf19da1387c47c660dbee5d`。
- 配置：`6db8e1247153e4066666e5dab21ba5ef89b6ceacb5169ec344daf60970aafc33`。
- 启动器：`0369d8977c9aa0ff0e1b7cee86b67cfa1a4224deb03b88e132ff54205db33b94`。

## 遗留边界

- 尚未运行真实 32 批实验，故无科学裁决、模型指标或资源读数。
- 实验若任何主门失败，入口只输出 `rejected_after_finite_step`；不调权、不折1、不重跑、不访问目标年份。
