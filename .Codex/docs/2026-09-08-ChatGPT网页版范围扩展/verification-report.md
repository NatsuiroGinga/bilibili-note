# 普通 ChatGPT 网页版范围扩展验证与部署报告

## 结论

项目规则、交接工作流、交接技能和通用 CLI/MCP 安装源已一致支持受限的 experiment-analysis。每个出站包只在创建/发送前执行一次机械敏感信息与越界路径预检；包内容不变即直接发送，只有内容变化或首次失败才重跑。网页端只能接收脱敏源期聚合摘要，所有输出固定为“外部候选，待本地全文和实验复核”。全局安装副本尚未部署。

## 已修改文件

- AGENTS.md：明确可交接任务、唯一的创建/发送前预检与必须留在 Codex 的核验、裁决、冻结和执行职责。
- .Codex/docs/ChatGPT交接工作流.md：定义脱敏源期摘要、唯一预检、禁止内容和固定外部候选标签。
- .codex/skills/chatgpt-handoff/SKILL.md：将网页任务、命令和一次预检边界同步到全局技能安装源。
- tools/chatgpt_handoff.py：新增受限 --task-type、experiment-analysis 必填 --sanitized-summary、敏感文本及路径拒绝和固定出站标签。
- scripts/chatgpt_handoff_mcp/server.py：在 MCP 清单和执行配置中公开任务类别、脱敏摘要是否存在，并同步白名单拒绝范围。
- scripts/chatgpt_handoff_mcp/smoke.py：新增源期摘要正例和全部敏感类别负例。
- scripts/chatgpt_handoff_mcp/README.md：记录通用任务类别、摘要接口、唯一预检和机械拒绝边界。

## 未修改文件

- 未修改任何实验代码、DRIFT 研究合同、服务器/GPU 状态、Git 远端状态或网页对话。
- 未修改 CLAUDE.md、scripts/chatgpt_handoff_mcp/install_global.sh、MCP 依赖锁文件或示例配置。
- 未直接修改 /Users/bilibili/.codex/skills/chatgpt-handoff/ 和 /Users/bilibili/.codex/tools/chatgpt-handoff/ 下的已安装全局副本。

## 验证证据

- 本轮执行 python -m py_compile tools/chatgpt_handoff.py scripts/chatgpt_handoff_mcp/server.py：通过。
- 本轮直接调用 CLI 预检函数：脱敏源期聚合摘要正例通过；目标期信息负例被拒绝。
- 已确认 create 在一次调用中仅验证路径清单和各个进入出站包的文本字段一次，MCP 不会重扫创建载荷。
- 本轮不运行全量烟雾矩阵、重复哈希比对或二次人工审查。

## 主代理部署清单



主代理确认后，在本工作树根执行已有的复制安装器：

~~~sh
bash scripts/chatgpt_handoff_mcp/install_global.sh
~~~

该安装器把项目内安装源复制到 /Users/bilibili/.codex/skills/chatgpt-handoff/ 与 /Users/bilibili/.codex/tools/chatgpt-handoff/ 对应路径；它未在本任务中执行。部署后不要求重复哈希、重复人工复审或全量烟雾测试。
