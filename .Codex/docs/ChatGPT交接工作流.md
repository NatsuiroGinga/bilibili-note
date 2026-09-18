# 普通 ChatGPT GitHub 半自动交接工作流

## 目的与边界

本流程把有界、只读、非代码执行的公开文献检索/综述/近邻排重、机制反例、脱敏源期实验汇总的二次分析、图表/笔记/草稿建议交给**普通 ChatGPT 对话**，减少 Codex 使用量。它不是原生子代理、共享文件系统或自动执行服务：ChatGPT 的结论一律标为“外部候选，待本地全文和实验复核”。

脱敏实验摘要只能包含源期的聚合指标、预先说明的比较口径和不含个体样本的文字结论。ChatGPT 只能提出二次分析、可视化或报告建议，不能验证哈希、日志或原始制品，不能判断实验有效性或候选存废，也不能改变冻结合同。

ChatGPT GitHub 应用按需读取已授权仓库内容，不创建同步索引；私有仓库必须由正确账户/组织安装应用并授予仓库访问权限，仓库显示可能约需五分钟。GitHub 应用只读，不能推送代码或 PR。[官方 GitHub 连接说明](https://help.openai.com/zh-hans-cn/articles/11145903-connecting-github-to-chatgpt)

Codex、ChatGPT Work、Workspace Agents 在可用套餐上共享使用额度；普通 Chat 使用不计入该共享代理额度。普通 Chat 能否使用 GitHub 取决于套餐和界面，不能用 Work、Workspace Agents 或 Codex 冒充“节省 Codex”。[官方 Codex 套餐与额度说明](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)

## 固定流程

1. Codex 用 `tools/chatgpt_handoff.py create` 生成出站 Markdown；该命令对路径和出站文本执行唯一一次机械敏感信息与越界路径预检。只列私有仓库、远端分支、提交、目标路径、任务类别、任务范围、证据状态、期望格式和禁用操作。脱敏实验二次分析使用 `--task-type experiment-analysis --sanitized-summary`，不得以文件、路径或日志替代摘要。
2. 预检通过且出站包内容未变时，安全提交并推送后由用户或获授权桌面操作直接把提示发到普通 ChatGPT 对话；不重复计算哈希、人工审查或运行第二次预检。只有出站包内容变化，或首次预检失败后修改内容，才重新执行 `create`。
3. 用户确认 GitHub 应用仅授权该私有仓库；ChatGPT 仅按提示检索已授权路径，不能写 Git、运行服务器/GPU、编辑仓库或访问未列路径。
4. 用户把 ChatGPT 输出原样复制到受管 inbox：`.Codex/docs/chatgpt-handoffs/inbox/`，附上出站包名与时间。
5. 回收输出原样保留为“外部候选，待本地全文和实验复核”，不得自动进入实验、恢复卡、论文或 Git 提交。该状态标记不触发额外的交接复审；只有后续实际引用该候选时，才按该产物所属的既有研究或写作规则处理。

本机 MCP 原型位于 `scripts/chatgpt_handoff_mcp/`，只提供 `list_handoffs`、`get_handoff`、`get_snapshot_manifest` 和受限 Markdown 搜索。它不能调用 ChatGPT；ChatGPT 只能通过远程端点或 Secure MCP Tunnel 连接，具体限制见 [MCP 原型报告](2026-09-07-ChatGPT-GitHub半自动交接/MCP原型报告.md)。

## 禁止内容

- 不复制原始数据、数据集、权重、检查点、日志、原始 PDF、缓存或大文件。
- 不发送 `.env`、令牌、密码、私钥、SSH 文件、连接串、服务器连接、个人绝对路径、用户数据或疑似秘密。
- 不发送未获 Codex 授权的目标期信息；脱敏实验摘要默认只允许源期聚合结果。
- 不把 ChatGPT 的建议当作实验结果、权威哈希/日志/原始制品核验、源码审查通过、文献全文核验或 Git 验收。
- 不让 ChatGPT 判断实验有效性、选择最终测试样本、阈值、超参数、候选存废或改写冻结合同。

## 出站包最小字段

- 私有仓库名与远端 URL 的公开标识。
- 远端分支、确切提交 SHA、目标文件路径和可读范围。
- 任务类别、任务边界、已知证据状态、期望 Markdown 格式和禁止操作。
- 若为实验二次分析，给出只含源期聚合结果的脱敏摘要，并说明禁止内容已剔除。
- 回收文件名与“外部候选，待本地全文和实验复核”的明确标记。

## 官方事实范围

- ChatGPT GitHub 连接是按需、只读检索；标准聊天是否可用因套餐和界面而异。[官方说明](https://help.openai.com/zh-hans-cn/articles/11145903-connecting-github-to-chatgpt)
- Work/Codex 与普通 Chat 的使用额度边界以上述套餐说明为准；模型在 Chat、Work、Codex 中的可用性也可能不同。[官方模型可用性说明](https://help.openai.com/en/articles/20001354-gpt-56-and-gpt-6-pro-in-chatgpt)
