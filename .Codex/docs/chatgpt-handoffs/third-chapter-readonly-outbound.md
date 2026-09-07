# ChatGPT 只读交接包

**状态：外部候选，未核验。**

## 仓库定位

- 私有仓库：`NatsuiroGinga/bilibili-note`
- 远端分支：`chatgpt/ch3-drift-20260907`
- 冻结提交：`f0ee98e`
- 允许读取路径：
  - `thesis/methods/第三章-DRIFT双侧漂移风险候选方案.md`
  - `thesis/methods/第三章-双分布对手博弈统一框架.md`
  - `thesis/experiments/llm_probe/tools/ch3_drift_bresnet_source_tail_diagnostic.py`
  - `thesis/experiments/llm_probe/tools/ch3_drift_bresnet_morphology_diagnostic.py`

## 任务

只读审查第三章条件风险资格探针的证据边界。

## 期望输出

返回 Markdown：结论、逐项证据（路径和行号）、不确定性、未回答问题。不得写代码、修改 GitHub、运行命令或访问未列路径。

## 禁止操作

不得输出秘密、凭据、SSH、数据、权重、检查点、日志、原始 PDF 或大文件内容。结果会进入受管 inbox，仍须由 Codex 独立复核。
