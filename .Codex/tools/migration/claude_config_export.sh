#!/usr/bin/env bash
# 扩展 1：把 ~/.claude 的「配置核心」导出到设备迁移暂存目录。
#
# 排除清单与断言全部内联在本脚本，不依赖人工「记得检查」；任一条失败即非零退出。
#
# 用法：
#   bash claude_config_export.sh [DEST_DIR]
#   默认 DEST_DIR = $HOME/device-migration/claude-config
set -euo pipefail

SRC="${HOME}/.claude"
DEST="${1:-${HOME}/device-migration/claude-config}"

# ── 白名单：只迁移这些条目（相对 ~/.claude） ──
# 注：settings.json 不在白名单。2026-10-13 盘点时其权限为 600、含 permissions/hooks/
#     enabledPlugins 等机器级配置与内部域名 cloud.bilibili.co；自动模式分类器将
#     「把该文件复制进仓库」判为敏感物化操作并阻断。按「不确定即排除」，改由新设备重建。
WHITELIST=(
  "rules"
  "hooks"
  "agents"
  "skills"
  "commands"
  "scripts"
  "templates"
  "CLAUDE.md"
  "AGENTS.md"
  "CLAUDE.zh-CN.md"
  "CLAUDE.scholar.md"
)

# plugins 只取用户态状态小文件；cache/ 与 marketplaces/ 是上游克隆、mcpmarket-me 是可
# 重装的第三方插件，均可在新设备重新拉取，故不复制。
PLUGINS_KEEP=(
  "installed_plugins.json"
  "known_marketplaces.json"
  "plugin-catalog-cache.json"
)

# ── 机械排除断言 1：DEST 任意深度禁止出现 ──
FORBIDDEN_NAMES=(
  "projects"
  "sessions"
  "shell-snapshots"
  "session-env"
  "file-history"
  "paste-cache"
  "daemon"
  "ide"
  "jobs"
  "skillctl"
  "history.jsonl"
  "mcp-needs-auth-cache.json"
  ".claude.json"
  "settings.json"
  "settings.local.json"
  "settings.bitto.json"
  "settings.claude.json"
  "settings.ollama.json"
  "claude-bitto"
)
FORBIDDEN_GLOBS=(
  "settings.json.bak*"
  "settings.json.before-fix"
  "CLAUDE.md.bak*"
  "*.bak-*"
  "*.bak"
  "*.bak.*"
  ".claude-scholar-*"
  ".last-cleanup"
  ".last-update-result.json"
  "*.sqlite"
  "*.sqlite-wal"
  "*.sqlite-shm"
  "*.sqlite-journal"
)

# ── 机械排除断言 2：文件内容不得匹配凭据模式 ──
# 注：允许出现「变量名」引用（如 GITHUB_PERSONAL_ACCESS_TOKEN 作为 env 键），
#     但不得出现任何具体的密钥值形态。
SECRET_RE='(ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16})'

die() { echo "GATE-FAIL: $*" >&2; exit 1; }

[ -d "$SRC" ] || die "源目录不存在：$SRC"

echo "== [1/6] 重置暂存目录 =="
rm -rf "$DEST"
mkdir -p "$DEST"

echo "== [2/6] 复制白名单项 =="
for item in "${WHITELIST[@]}"; do
  if [ -e "$SRC/$item" ]; then
    cp -R "$SRC/$item" "$DEST/$item"; echo "  copied: $item"
  else
    echo "  (skip, absent): $item"
  fi
done

echo "== [3/6] 复制 plugins 用户态子集 =="
mkdir -p "$DEST/plugins"
for item in "${PLUGINS_KEEP[@]}"; do
  if [ -e "$SRC/plugins/$item" ]; then
    cp -R "$SRC/plugins/$item" "$DEST/plugins/$item"; echo "  copied: plugins/$item"
  else
    echo "  (skip, absent): plugins/$item"
  fi
done

echo "== [4/6] 清理备份与可再生噪声 =="
find "$DEST" -name 'node_modules' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$DEST" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$DEST" -type f -name '*.bak' -delete 2>/dev/null || true
find "$DEST" -type f -name '*.bak-*' -delete 2>/dev/null || true
find "$DEST" -type f -name '*.bak.*' -delete 2>/dev/null || true

echo "== [5/6] 断言：排除清单未泄漏到 DEST =="
for name in "${FORBIDDEN_NAMES[@]}"; do
  hit="$(find "$DEST" -name "$name" -print -quit 2>/dev/null || true)"
  [ -z "$hit" ] || die "排除项泄漏：$hit"
done
for g in "${FORBIDDEN_GLOBS[@]}"; do
  hit="$(find "$DEST" -name "$g" -print -quit 2>/dev/null || true)"
  [ -z "$hit" ] || die "排除项泄漏：$hit"
done
for d in cache marketplaces data; do
  [ -e "$DEST/plugins/$d" ] && die "plugins/$d 不应被复制（可再生上游克隆）"
done
echo "  OK: 无排除项"

echo "== [6/6] 断言：DEST 内容不含凭据值形态 =="
if hits="$(grep -rIlE "$SECRET_RE" "$DEST" 2>/dev/null)"; then
  [ -z "$hits" ] || { echo "$hits" >&2; die "内容命中凭据值形态（上方文件）"; }
fi
echo "  OK: 无凭据值命中"

echo
echo "PASS: ~/.claude 配置核心已导出到 $DEST"
echo "文件总数：$(find "$DEST" -type f | wc -l | tr -d ' ')"
echo "总大小：$(du -sh "$DEST" | cut -f1)"
