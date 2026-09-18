# ChatGPT 通用只读交接 MCP

该工具为任意 Git 工作树提供受管出站包、执行配置和白名单 Markdown 检索。它不调用 ChatGPT、不写 Git、不访问服务器、原始数据、数据集、权重、检查点、日志或其他实验制品。所有网页输出都是“外部候选，待本地全文和实验复核”。

先初始化目标项目：

```sh
python tools/chatgpt_handoff.py init --project-root /path/to/repo
```

生成带模型、思考强度、模式和应用配置的出站包：

```sh
python tools/chatgpt_handoff.py create \
  --project-root /path/to/repo \
  --name literature-review \
  --paths /path/to/paths.txt \
  --task-type experiment-analysis \
  --sanitized-summary "源期聚合指标：模型 A 的召回率 0.81，模型 B 的召回率 0.79。" \
  --task "仅对脱敏源期汇总提出二次分析和图表建议" \
  --model auto \
  --effort high \
  --mode deep-research \
  --apps github,zotero
```

启动 MCP：

```sh
uv run --project scripts/chatgpt_handoff_mcp python server.py \
  --project-root /path/to/repo \
  --host 127.0.0.1 \
  --port 8123
```

MCP 提供：

- `list_handoffs`
- `get_handoff`
- `get_snapshot_manifest`
- `get_execution_profile`
- `search_handoff_context`

`create` 的 `--task-type` 仅允许 `literature-search`、`literature-review`、`neighbor-deduplication`、`mechanism-counterexample`、`experiment-analysis`、`figure-suggestion`、`note-suggestion` 和 `draft-suggestion`。`experiment-analysis` 必须提供 `--sanitized-summary`，且该摘要只能是源期聚合信息。CLI 会在创建时唯一一次拒绝原始数据或数据集、检查点或权重、日志、凭据、服务器连接、个人绝对路径、目标期信息和越界路径；包内容未变时直接发送，不再进行第二次扫描。

本地 `127.0.0.1` 端点不能被 ChatGPT 直接连接；端到端接入需要符合套餐权限的远程端点或 Secure MCP Tunnel。示例配置见 `mcp-config.example.json`。
