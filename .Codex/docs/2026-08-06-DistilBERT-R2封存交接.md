# DistilBERT R2 封存交接

- 状态：已终止后续实验，仅保留历史结构诊断。
- 服务器实况：种子 42 的 `F-A/F-P/F-S` 均已正常结束；当前无 DistilBERT 训练进程和持久会话。
- 禁止事项：不启动种子 43、44，不新增 DistilBERT 对照组，不修改或删除既有代码、配置、日志、SwanLab 运行、检查点和结果。
- 历史结论：`F-P` 开发验证宏平均 F1 为 `0.9090792054`，高于 `F-S` 但低于 `F-A`；状态误差恶化，物理残差改善未达到 `10%`。该结果只说明旧结构的失败边界，不再作为 Qwen3-0.6B 正式实验的前置门禁。
- 服务器制品：`runs/r2-minimal-sidecar-probe/distilbert-identifiable-g3mask-v3/seed-42/`。
- 详细证据：[R2 TCP 修正版种子 42 GPU 重跑报告](2026-08-05-R2-TCP修正版种子42GPU重跑报告.md)。

