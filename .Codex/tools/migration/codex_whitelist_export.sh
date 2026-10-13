#!/usr/bin/env bash
# B2：把 ~/.codex 的白名单内容导出到迁移暂存目录。
#
# 设计原则（AGENTS.md「实验工程开发范式」）：
#   排除清单是脚本内的机械断言，不依赖人工「记得检查」。
#   任一条断言失败 -> 立即退出非零并打印诊断；通过 -> 进入下一阶段。
#
# 用法：
#   bash codex_whitelist_export.sh [DEST_DIR]
#   默认 DEST_DIR = $HOME/device-migration/codex-config
#
# 幂等性：先清空 DEST 再复制；重复执行结果一致。
set -euo pipefail

SRC="${HOME}/.codex"
DEST="${1:-${HOME}/device-migration/codex-config}"

# ── 白名单：只迁移这些子目录/文件（相对 ~/.codex） ──
WHITELIST=(
  "skills"
  "memories"
  "agents"
  "hooks"
  "rules"
  "templates"
  "AGENTS.md"
  "AGENTS.zh-CN.md"
  "AGENTS.scholar.md"
)

# ── 机械排除断言 1a：仅限 DEST 顶层，禁止出现（凭据/机器级配置文件本身） ──
TOP_FORBIDDEN_NAMES=(
  "config.toml"
  "auth.json"
  ".codex-global-state.json"
  "installation_id"
  "chrome-native-hosts-v2.json"
  "history.jsonl"
  "session_index.jsonl"
)
# 顶层禁止的备份变体（config.toml.bak / config.toml.bak.*）
TOP_FORBIDDEN_GLOBS=(
  "config.toml.bak*"
  ".codex-global-state.json.*"
  "..codex-global-state.json.tmp-*"
)

# ── 机械排除断言 1b：DEST 任意深度禁止出现 ──
FORBIDDEN_NAMES=(
  "auth.json"
  "shell_snapshots"
  "sessions"
  "mcp-oauth-locks"
  "chrome-native-hosts-v2.json"
  "external_agent_session_imports.json"
  "history.jsonl"
  "session_index.jsonl"
  "installation_id"
  "packages"
  "plugins"
  "releases"
  "computer-use"
  "browser"
  "attachments"
  "generated_images"
  "vendor_imports"
  "skill-archives"
)
FORBIDDEN_GLOBS=(
  "*.sqlite"
  "*.sqlite-wal"
  "*.sqlite-shm"
  "*.sqlite-journal"
  ".codex-scholar-*"
)

# ── 机械排除断言 2：文件内容不得匹配凭据模式 ──
SECRET_RE='(ANTHROPIC_AUTH_TOKEN|GITHUB_PERSONAL_ACCESS_TOKEN|GITLAB_TOKEN|ZOTERO_API_KEY|bearer_token|BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,})'

die() { echo "GATE-FAIL: $*" >&2; exit 1; }

[ -d "$SRC" ] || die "源目录不存在：$SRC"

echo "== [1/5] 重置暂存目录 =="
rm -rf "$DEST"
mkdir -p "$DEST"

echo "== [2/5] 复制白名单项 =="
for item in "${WHITELIST[@]}"; do
  if [ -e "$SRC/$item" ]; then
    cp -R "$SRC/$item" "$DEST/$item"
    echo "  copied: $item"
  else
    echo "  (skip, absent): $item"
  fi
done

echo "== [3/5] 清理可再生/备份噪声（*.bak / node_modules / __pycache__） =="
find "$DEST" -name 'node_modules' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$DEST" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$DEST" -type f -name '*.bak' -delete 2>/dev/null || true
find "$DEST" -type f -name '*.bak.*' -delete 2>/dev/null || true

echo "== [4/5] 断言：排除清单未泄漏到 DEST =="
for name in "${TOP_FORBIDDEN_NAMES[@]}"; do
  hit="$(find "$DEST" -maxdepth 1 -name "$name" -print -quit 2>/dev/null || true)"
  [ -z "$hit" ] || die "排除项泄漏（顶层）：$hit"
done
for g in "${TOP_FORBIDDEN_GLOBS[@]}"; do
  hit="$(find "$DEST" -maxdepth 1 -name "$g" -print -quit 2>/dev/null || true)"
  [ -z "$hit" ] || die "排除项泄漏（顶层）：$hit"
done
for name in "${FORBIDDEN_NAMES[@]}"; do
  hit="$(find "$DEST" -name "$name" -print -quit 2>/dev/null || true)"
  [ -z "$hit" ] || die "排除项泄漏：$hit"
done
for g in "${FORBIDDEN_GLOBS[@]}"; do
  hit="$(find "$DEST" -name "$g" -print -quit 2>/dev/null || true)"
  [ -z "$hit" ] || die "排除项泄漏：$hit"
done
echo "  OK: 无排除项"

echo "== [5/5] 断言：DEST 内容不含凭据模式 =="
if hits="$(grep -rIlE "$SECRET_RE" "$DEST" 2>/dev/null)"; then
  [ -z "$hits" ] || { echo "$hits" >&2; die "内容命中凭据模式（上方文件）"; }
fi
echo "  OK: 无凭据模式命中"

echo
echo "PASS: 白名单已导出到 $DEST"
echo "文件总数：$(find "$DEST" -type f | wc -l | tr -d ' ')"
echo "总大小：$(du -sh "$DEST" | cut -f1)"
