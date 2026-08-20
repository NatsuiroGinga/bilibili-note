# PBC 父运行恢复证明修复证据记录

## 父运行状态

- 父运行：`ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1`
- 历史状态：`running/source_selection/exit_code=null`
- 实际中断点：LSPR24 `semantic168` 前缀构造约 81.6%。
- 缺失：`xgb_cpa_elp_results.json`、原始 `manifest.json`。
- 现存：选择收据、有效配置收据、三种表示的九个折外模型、两个全量模型。
- 11 个模型的树数均为 800；有效配置收据 11 项全部通过。

## PBC 实际输入依赖

- `selection_frozen_xgb2x2.json`
- `effective_config_receipts.json`
- `model_raw83.json`
- `model_semantic168.json`
- `model_oof_semantic168_fold0.json`
- `model_oof_semantic168_fold1.json`
- `model_oof_semantic168_fold2.json`
- 已完成的独立父评价运行 `ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-eval-continuation2` 的结果、清单和状态。

## 研究诚信边界

- 不能把根据现存文件重建的兼容内容写回父根并命名为原始 `manifest.json`。
- 可以新增独立恢复证明，但必须明确它是事后核验制品，不是历史运行原生清单。
- 恢复证明只证明输入模型身份和完整性，不把中断父运行改写为“完整成功”。

## 错误记录

- 旧会话临时入口 `/tmp/gpu-exec.exp` 已不存在；后续只使用仓库内正式远程入口 `thesis/experiments/llm_probe/tools/remote_exec/gpu_env_quiet.exp`。
- 当前本机未设置 `GPU_SSH_ACTIVE`；远端动作前应从当前服务器对应环境变量建立进程内别名，不得打印变量值。
