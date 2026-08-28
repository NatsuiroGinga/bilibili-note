# 严格过去 CPA 曲线横轴根因修复实施报告

## 结论

严格过去 CPA 协议 A Q0 的源年汇总错误已按冻结科学合同修复，生产入口已具备同步和启动条件。当前仅完成代码与静态验收，尚未运行 `rerun1`，因此不能宣称源门或目标年评价结果。

新运行身份为 `ch3-full-mlp-strict-past-cpa-protocol-a-q0-seed42-v1-rerun1`。旧失败运行只读保留；新入口不会调用训练函数，只复用旧运行已封印的 S10/S11 选中检查点，重做源年门，并仅在源门通过后读取目标年。

## 根因与统计口径

父函数按每个模型自身的负实体分数阈值生成完整曲线。分数并列时，一次阈值会同时纳入整组负实体，因此不同模型的 `realized_fpr` 可达点不必逐位相同。原入口错误执行 `np.array_equal(candidate_x, baseline_x)`，在 S10 与 B10 首对比较时终止。

修复后：

1. 完整曲线面积继续分别对每个模型自身的可达阶梯在 `0%–8% FPR` 上积分，再比较归一化面积；该预注册门槛不变。
2. 公共目标误报率继续使用冻结的 `0.1%/0.5%/1%/2%/4%/8%` 六档检测率；门禁仍只要求 4% 与 8% 不下降。
3. 不执行线性插值，不把一个模型不可达的阈值性能制造出来。
4. 删除不属于预注册门禁、且依赖错误公共可达横轴的逐点优势比例与伤害比例。实体 AP、逐流 AP、六档检测率、长度桶、完整曲线及曲线面积均保留。

## 旧运行复用门

生产工具在复制检查点前机械核验：

- 旧状态必须为 `failed/exit=1`，错误必须精确为 `S10_vs_B10 完整预算曲线横轴不一致`，且 `target_year_arrays_read=0`。
- 旧冻结配置、旧输入配置与旧代码 SHA-256 必须匹配冻结恢复合同。
- 旧启动器输入摘要必须把配置与工具路径分别绑定到对应 SHA-256。
- S10/S11 各自的选择收据、选中检查点 SHA-256、检查点内部身份必须一致。
- S10/S11 各自必须保留从第 1 轮到第 20 轮的完整逐轮检查点。
- 旧运行与 `rerun1` 的模型、源/目标数组、单元、候选、训练、评价和证据身份必须相同。
- 当前源数据清单必须与旧训练身份和父对照身份相同。

核验通过后只复制两个选中检查点到新运行根。新目录写 `training-reuse-receipt.json` 与两个 `reuse-selection-*.json`；旧 40 个逐轮检查点不复制、不修改。汇总结果明确记录 `new_training_cells=0`、`previous_training_cells_reused=2` 与 `rerun_training_wall_seconds=0`。

## 变更文件

- `thesis/experiments/llm_probe/tools/ch3_full_mlp_strict_past_cpa_protocol_a_q0.py`
- `thesis/experiments/llm_probe/configs/ch3-full-mlp-strict-past-cpa-protocol-a-q0-seed42-v1.json`
- `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_full_mlp_strict_past_cpa_protocol_a_q0_seed42_v1.sh`
- `.Codex/docs/RWKV/2026-08-20-严格过去CPA曲线横轴根因修复/task_plan.md`
- `.Codex/docs/RWKV/2026-08-20-严格过去CPA曲线横轴根因修复/notes.md`
- `.Codex/docs/RWKV/2026-08-20-严格过去CPA曲线横轴根因修复/implementation-report.md`

未修改父完整实体 Q0 工具、父配置、旧失败运行目录、恢复卡、路线总控、实验台账或目标年制品。

## 静态验收

2026-08-20 集中执行一次：

| 检查 | 结果 |
| --- | --- |
| `git diff --check` | 通过，退出码 0 |
| Python 内建编译 | 通过，退出码 0 |
| 模块导入 | 通过，退出码 0 |
| `--help` | 通过，退出码 0 |
| 冻结配置核验 | 通过，退出码 0，输出“配置核验通过” |
| 启动器 `bash -n` | 通过，退出码 0 |

未运行 `black`、测试夹具、独立冒烟实验、训练、源年评价或目标年评价。

## 当前生产文件 SHA-256

| 文件 | SHA-256 |
| --- | --- |
| `tools/ch3_full_mlp_strict_past_cpa_protocol_a_q0.py` | `f0dd560586d56111be2a7efc131273029b3fcde385f06b6eff8455e9ad767fe4` |
| `configs/ch3-full-mlp-strict-past-cpa-protocol-a-q0-seed42-v1.json` | `e4c3d8ade519c6b9bda921986a6596a717d7554045cb9914dc918da5fcfdb05e` |
| `scripts/remote_launchers/run_ch3_full_mlp_strict_past_cpa_protocol_a_q0_seed42_v1.sh` | `201187d9a0feaeeba5c506f01996b414975753dcf274e1bbfdbb55da9486c4e3` |

## 交付边界

共享暂存区已有其他任务文件，本任务未暂存、提交或回滚任何内容。主进程负责同步上述三个生产文件，并用现有启动器启动 `rerun1`。运行前仍须核验 B76 当前身份、资源、输入与 SwanLab 目的地；运行完成或明确异常前不读取目标结果。

实现代理：`strict_past_curve_axis_fix_sol_high`；模型：`gpt-5.6-sol`；推理强度：`high`。
