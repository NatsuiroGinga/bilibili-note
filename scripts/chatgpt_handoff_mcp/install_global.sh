#!/bin/bash
# 将通用交接 CLI、MCP 与 Skill 安装到用户级 Codex 目录。

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
TARGET="$CODEX_HOME/tools/chatgpt-handoff"
SKILL_TARGET="$CODEX_HOME/skills/chatgpt-handoff"

mkdir -p "$TARGET/mcp" "$SKILL_TARGET"
install -m 0755 "$ROOT/tools/chatgpt_handoff.py" "$TARGET/chatgpt_handoff.py"
install -m 0644 "$ROOT/.codex/skills/chatgpt-handoff/SKILL.md" "$SKILL_TARGET/SKILL.md"

for file in pyproject.toml uv.lock server.py smoke.py README.md mcp-config.example.json; do
  install -m 0644 "$ROOT/scripts/chatgpt_handoff_mcp/$file" "$TARGET/mcp/$file"
done

printf '已安装 CLI：%s\n' "$TARGET/chatgpt_handoff.py"
printf '已安装 MCP：%s\n' "$TARGET/mcp"
printf '已安装 Skill：%s\n' "$SKILL_TARGET/SKILL.md"
printf '新会话启动后发现全局 Skill。\n'
