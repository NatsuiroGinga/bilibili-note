# 运行产物

每次运行保存配置快照、数据清单、环境版本、训练摘要、评估摘要和失败记录。模型检查点、优化器状态与逐样本大日志不进入版本管理。

在线训练和评估的最低制品集合为 `console.log`、阶段专属 `swanlog/`、`swanlab_metrics.json`、结果文件和 `artifact_manifest.json`。制品清单必须记录 SwanLab 运行编号、公开链接、服务端路径和本地归档路径；已有清单的输出目录不得复用。

SwanLab 诊断运行统一归档在 `swanlab-diagnostics/`。其中 `tracking-layer-artifact-smoke/` 保存标准跟踪层的云端接口结果、原始日志、独立运行清单与网页图表截图。
