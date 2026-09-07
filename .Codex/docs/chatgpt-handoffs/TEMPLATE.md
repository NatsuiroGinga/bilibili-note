# ChatGPT 只读交接包

**状态：外部候选，未核验。**

## 仓库定位

- 私有仓库：`<owner/repository>`
- 远端分支：`<remote-branch>`
- 冻结提交：`<commit-sha>`
- 允许读取路径：`<one-path-per-line>`

## 任务

`<bounded read-only task>`

## 已知证据状态

`<what is verified, what remains a hypothesis>`

## 期望输出

请返回 Markdown，包含：结论、逐项证据（文件路径与行号）、不确定性、未回答问题。不要写代码、创建 PR、修改 GitHub、运行命令、访问未列路径，或把推测写为实验事实。

## 禁止信息

不要索取或输出秘密、`.env`、凭据、SSH、数据、权重、检查点、日志、原始 PDF 或大文件内容。

## Codex 回收核验

输出会复制到 `.Codex/docs/chatgpt-handoffs/inbox/`，并由 Codex 独立核对提交、引用路径、原始证据和冻结合同后才可使用。
