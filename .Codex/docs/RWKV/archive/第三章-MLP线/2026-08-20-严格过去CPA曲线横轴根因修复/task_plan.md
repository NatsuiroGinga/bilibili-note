# 严格过去 CPA 曲线横轴根因修复计划

## 目标

修复严格过去 CPA 协议 A Q0 在源年汇总阶段错误要求不同模型可达误报率横轴逐位相同的问题，以新运行身份 `ch3-full-mlp-strict-past-cpa-protocol-a-q0-seed42-v1-rerun1` 复用旧失败运行已完成的 S10/S11 训练制品，不重训、不改变科学合同，并继续保持源门通过前目标年数组零读取。

## 阶段

- [x] 核对规则、冻结计划、父完整实体 Q0 曲线实现和旧失败运行原始状态。
- [x] 确认根因与统计口径：各模型按自身可达阶梯积分，公共目标误报率只读冻结六档指标，不做线性插值。
- [ ] 实现旧训练制品机械核验、迁移收据和 `rerun1` 恢复入口。
- [ ] 执行一次语法、导入、帮助、配置与 Shell 静态验收。
- [ ] 写实施报告并向主代理交付同步和启动路径。

## 文件边界

- `thesis/experiments/llm_probe/tools/ch3_full_mlp_strict_past_cpa_protocol_a_q0.py`
- `thesis/experiments/llm_probe/configs/ch3-full-mlp-strict-past-cpa-protocol-a-q0-seed42-v1.json`
- `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_full_mlp_strict_past_cpa_protocol_a_q0_seed42_v1.sh`
- `.Codex/docs/RWKV/2026-08-20-严格过去CPA曲线横轴根因修复/`

## 验收

1. Python 内建编译检查。
2. 模块导入检查。
3. `--help` 检查。
4. 冻结配置核验。
5. 启动器 `bash -n`。

不运行测试夹具、独立冒烟实验、训练或目标年评价；主进程负责同步和正式启动。

## 阻塞条件

- 旧失败状态、输入身份、选择收据、选中检查点或 20 轮检查点不完整时拒绝复用。
- 旧失败运行目标年读取数不是 0 时拒绝复用。
- 当前源数据清单与旧选择身份不一致时拒绝复用。
- `rerun1` 输出根已有不兼容制品时拒绝覆盖。

## 当前状态

正在实现阶段；共享暂存区非空，本任务不提交。
