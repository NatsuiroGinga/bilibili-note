# 普通 ChatGPT GitHub 半自动交接工作流

## 目的与边界

本流程把有界、只读、非代码执行的文献综合、机制构思、理论审查或正文草稿交给**普通 ChatGPT 对话**，减少 Codex 使用量。它不是原生子代理、共享文件系统或自动执行服务：ChatGPT 的结论是外部候选，必须回收后由 Codex 独立复核。

ChatGPT GitHub 应用按需读取已授权仓库内容，不创建同步索引；私有仓库必须由正确账户/组织安装应用并授予仓库访问权限，仓库显示可能约需五分钟。GitHub 应用只读，不能推送代码或 PR。[官方 GitHub 连接说明](https://help.openai.com/zh-hans-cn/articles/11145903-connecting-github-to-chatgpt)

Codex、ChatGPT Work、Workspace Agents 在可用套餐上共享使用额度；普通 Chat 使用不计入该共享代理额度。普通 Chat 能否使用 GitHub 取决于套餐和界面，不能用 Work、Workspace Agents 或 Codex 冒充“节省 Codex”。[官方 Codex 套餐与额度说明](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)

## 固定流程

1. Codex 用 `tools/chatgpt_handoff.py create` 生成出站 Markdown，只列私有仓库、远端分支、提交、目标路径、任务范围、证据状态、期望格式和禁用操作。
2. Codex 对拟引用文件做显式路径审查，安全提交并推送后，用户或获授权桌面操作把出站提示发到普通 ChatGPT 对话。
3. 用户确认 GitHub 应用仅授权该私有仓库；ChatGPT 仅按提示检索已授权路径，不能写 Git、运行服务器/GPU、编辑仓库或访问未列路径。
4. 用户把 ChatGPT 输出原样复制到受管 inbox：`.Codex/docs/chatgpt-handoffs/inbox/`，附上出站包名与时间。
5. Codex 独立核对引用的分支/提交、文件、原始制品和研究合同；未经核验的外部文字只能标为候选，不得进入实验、恢复卡、论文或 Git 提交。

## 禁止内容

- 不复制数据、权重、检查点、日志、原始 PDF、缓存或大文件。
- 不发送 `.env`、令牌、密码、私钥、SSH 文件、连接串、用户数据或疑似秘密。
- 不把 ChatGPT 的建议当作实验结果、源码审查通过、文献全文核验或 Git 验收。
- 不让 ChatGPT 选择最终测试样本、阈值、超参数、候选存废或改写冻结合同。

## 出站包最小字段

- 私有仓库名与远端 URL 的公开标识。
- 远端分支、确切提交 SHA、目标文件路径和可读范围。
- 任务边界、已知证据状态、期望 Markdown 格式和禁止操作。
- 回收文件名、Codex 复核项与“外部候选，未核验”的明确标记。

## 官方事实范围

- ChatGPT GitHub 连接是按需、只读检索；标准聊天是否可用因套餐和界面而异。[官方说明](https://help.openai.com/zh-hans-cn/articles/11145903-connecting-github-to-chatgpt)
- Work/Codex 与普通 Chat 的使用额度边界以上述套餐说明为准；模型在 Chat、Work、Codex 中的可用性也可能不同。[官方模型可用性说明](https://help.openai.com/en/articles/20001354-gpt-56-and-gpt-6-pro-in-chatgpt)
