# 普通 ChatGPT 网页版范围扩展实施计划

## 目标

在项目规则、交接技能与通用只读 CLI/MCP 中一致表达普通 ChatGPT 网页版可处理的只读候选任务，并在创建出站包时机械拒绝可识别的敏感载荷。ChatGPT 的所有输出保持“外部候选，待本地全文和实验复核”状态。

## 范围与所有权

- 可修改：根 `AGENTS.md` 的 ChatGPT 规则、`.Codex/docs/ChatGPT交接工作流.md`、项目内交接工具源 `tools/chatgpt_handoff.py` 与 `scripts/chatgpt_handoff_mcp/`、项目内技能源 `.codex/skills/chatgpt-handoff/SKILL.md`、本目录过程记录。
- 全局安装副本：`/Users/bilibili/.codex/skills/chatgpt-handoff/` 与 `/Users/bilibili/.codex/tools/chatgpt-handoff/`。本代理不直接部署；由主代理在确认后运行项目内 `scripts/chatgpt_handoff_mcp/install_global.sh`。
- 不修改：实验代码、DRIFT 研究合同、服务器或 Git 远程状态。

## 冻结边界

- 可交接：公开文献检索/综述/近邻排重、机制反例、脱敏源期实验汇总的二次分析、图表/笔记/草稿建议。
- 留在 Codex：权威哈希、日志和原始制品核验，实验有效性与存废裁决，冻结合同，代码，服务器/GPU，Git 写操作。
- 出站包必须拒绝：原始数据、数据集、检查点/权重、日志、凭据、服务器连接、个人绝对路径、未授权目标期信息。

## 实施阶段

- [x] 阶段 1：阅读技能、现有工作流及 CLI/MCP 源码，冻结边界。
- [x] 阶段 2：更新项目规则、工作流、技能和通用源代码。
- [x] 阶段 3：确认 CLI/MCP 的创建路径仅扫描一次载荷；运行最小语法与一正一负预检验证。
- [x] 阶段 4：记录验证和全局部署清单，交主代理验收。

## 验收命令

- `python -m py_compile tools/chatgpt_handoff.py scripts/chatgpt_handoff_mcp/server.py`
- 直接调用预检函数的一条脱敏源期正例和一条目标期负例。
- 不运行全量烟雾矩阵；包内容未变时不重复预检。

## 当前状态

一次预检裁决已完成：CLI/MCP 实现未改，因为创建路径本来只扫描一次；规则、技能、工作流、MCP 文档和验证报告已删除重复预检要求。全局安装副本未直接写入，等待主代理按验证报告执行既有安装脚本。
