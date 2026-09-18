# ChatGPT 只读 MCP 原型报告

## 实施计划

1. 创建独立 uv 项目，使用 Python MCP SDK 在 `127.0.0.1` 提供只读服务。
2. 仅枚举 `*-outbound.md`，以路径 SHA256 截断值作为稳定 ID；所有读取均经白名单验证。
3. 提供 `list_handoffs`、`get_handoff`、`get_snapshot_manifest` 与受限 Markdown 搜索，不暴露任意路径、shell、Git、服务器或数据访问。
4. 用 SDK stdio 客户端完成真实初始化、工具列举、调用与路径穿越拒绝；不把本地通过误写成 ChatGPT 已连接。

## 官方边界

ChatGPT 不能直接连接本地 MCP；私网或开发机服务需 Secure MCP Tunnel。Pro 目前仅可用 read/fetch，完整 MCP 写入只向 Business、Enterprise/Edu 提供。来源：[OpenAI 官方说明](https://help.openai.com/en/articles/12584461)。

## 验证

- `py_compile server.py smoke.py` 通过。
- `uv run python server.py --help` 通过。
- `uv run python smoke.py` 完成真实 stdio MCP 初始化、`list_tools`、`list_handoffs` 调用和路径穿越 ID 拒绝。
- `--host 0.0.0.0` 被服务拒绝；服务只接受 `127.0.0.1`。
- 本地原型完成不等于 ChatGPT 端已连接；端到端接入仍需用户套餐支持、远程端点或 Secure MCP Tunnel。
