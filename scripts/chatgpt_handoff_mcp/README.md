# ChatGPT 通用只读交接 MCP

该工具为任意 Git 工作树提供受管出站包、执行配置和白名单 Markdown 检索。它不调用 ChatGPT、不写 Git、不访问服务器、数据或实验制品。

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
  --task "只读完成文献综述" \
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

本地 `127.0.0.1` 端点不能被 ChatGPT 直接连接；端到端接入需要符合套餐权限的远程端点或 Secure MCP Tunnel。示例配置见 `mcp-config.example.json`。
