# MPS 首批分段诊断修复简报

## 已有证据

2026-09-23 的四阶段真实迁移诊断在清理非 DRIFT 资源后完成：模型构造 `0.2808s`、权重读取 `0.1009s`、状态写入 `0.0176s`、迁移并同步 MPS `0.4234s`。因此当前不能将 CPU `map_location` 或 `.to(mps)` 写成稳定启动瓶颈。

旧全阶段工具已具备真实 T17 开发批、首前向和首反向阶段，但启动器预建 `console.log` 时会错误拒绝非空运行目录；其技能收据也未采用当前统一模板。

## 唯一修复

仅修改 `thesis/experiments/llm_probe/tools/ch3_drift_mps_startup_diagnostic.py`，以及本目录 `mps-startup-diagnostic-report.md`、`mps-startup-diagnostic-skill-receipt.json`：

1. 路径门禁允许运行目录只预存一个常规 `console.log`，保留内容；其他文件、目录、符号链接或 `.partial` 仍失败关闭。
2. 元数据路径改为相对仓库根；收据使用当前可读技能路径、哈希、完整命令和统一字段。
3. 保持既有七阶段、真实总批128（T17两类各64）、`torch.mps.synchronize()`、阶段先写`running`状态的语义不变。

不修改模型、嵌套张量、CPU加载、训练脚本、数据合同或攻击算子；不由实现代理运行 MPS。主代理随后以 `PYTORCH_ENABLE_MPS_FALLBACK=1` 在新目录运行，目的是判断首前向或首反向是否为卡点，不产生训练或方法效果结论。
