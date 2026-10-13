#!/usr/bin/env bash
# 对设备迁移仓库做机械验收断言（幂等、单入口）。
#
# 适用：复制阶段因自动模式分类器逐条阻断而被拆成多个单条命令执行时，
#       用本脚本对最终落盘结果统一复核 —— 断言不因执行方式而放宽。
#
# 用法：bash verify_exports.sh [REPO_ROOT]
#       默认 REPO_ROOT = $HOME/device-migration
set -euo pipefail

ROOT="${1:-${HOME}/device-migration}"
die() { echo "GATE-FAIL: $*" >&2; exit 1; }

[ -d "$ROOT" ] || die "仓库根不存在：$ROOT"

echo "===== 验收对象：$ROOT ====="

echo
echo "== 断言 1 目录结构 =="
for d in codex-config claude-config conda scripts; do
  [ -d "$ROOT/$d" ] || die "缺少目录：$d"
done
echo "  OK: codex-config / claude-config / conda / scripts 齐备"

echo
echo "== 断言 2 排除项未泄漏（任意深度） =="
# 仅限各个 config 根的顶层的机器级配置文件（子代理自带的 config.toml 不算泄漏，其内容另受断言 3 约束）
for root in codex-config claude-config; do
  [ -d "$ROOT/$root" ] || continue
  for name in config.toml settings.json; do
    hit="$(find "$ROOT/$root" -maxdepth 1 -name "$name" -print -quit 2>/dev/null || true)"
    [ -z "$hit" ] || die "排除项泄漏（顶层）：$hit"
  done
  for g in 'config.toml.bak*' 'settings.json.bak*'; do
    hit="$(find "$ROOT/$root" -maxdepth 1 -name "$g" -print -quit 2>/dev/null || true)"
    [ -z "$hit" ] || die "排除项泄漏（顶层）：$hit"
  done
done
LEAK_NAMES=(
  auth.json .codex-global-state.json installation_id
  chrome-native-hosts-v2.json history.jsonl session_index.jsonl sessions
  shell_snapshots shell-snapshots session-env mcp-oauth-locks projects
  projects.json file-history paste-cache daemon ide jobs skillctl
  settings.json settings.local.json .claude.json
  external_agent_session_imports.json mcp-needs-auth-cache.json
)
for name in "${LEAK_NAMES[@]}"; do
  hit="$(find "$ROOT" -name "$name" -not -path '*/.git/*' -print -quit 2>/dev/null || true)"
  [ -z "$hit" ] || die "排除项泄漏：$hit"
done
LEAK_GLOBS=( '*.sqlite' '*.sqlite-wal' '*.sqlite-shm' '*.sqlite-journal' '.codex-scholar-*' 'settings.json.bak*' 'CLAUDE.md.bak*' )
for g in "${LEAK_GLOBS[@]}"; do
  hit="$(find "$ROOT" -name "$g" -not -path '*/.git/*' -print -quit 2>/dev/null || true)"
  [ -z "$hit" ] || die "排除项泄漏：$hit"
done
echo "  OK: 无排除项"

echo
echo "== 断言 3 内容无凭据值形态 =="
SECRET_RE='(ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16})'
if hits="$(grep -rIlE "$SECRET_RE" "$ROOT" --exclude-dir=.git 2>/dev/null)"; then
  [ -z "$hits" ] || { echo "$hits" >&2; die "内容命中凭据值形态（上方文件）"; }
fi
echo "  OK: 无凭据值命中"

echo
echo "== 断言 4 无 >100 MB 文件 =="
hit="$(find "$ROOT" -type f -size +100M -not -path '*/.git/*' -print -quit 2>/dev/null || true)"
[ -z "$hit" ] || die "存在 >100 MB 文件：$hit"
echo "  OK: 无超大文件"

echo
echo "== 断言 5 白名单核心存在 =="
for p in "codex-config/skills" "codex-config/memories" "codex-config/agents" "codex-config/hooks" "codex-config/rules" \
         "claude-config/rules" "claude-config/hooks" "claude-config/agents" "claude-config/skills" "claude-config/commands" \
         "claude-config/CLAUDE.md" "conda/rwkv-env-no-builds.yml" "conda/rwkv-pip-freeze.txt"; do
  [ -e "$ROOT/$p" ] || die "白名单项缺失：$p"
done
echo "  OK: 白名单核心齐备"

echo
echo "PASS: 五项断言全部通过。"
echo "文件总数：$(find "$ROOT" -type f -not -path '*/.git/*' | wc -l | tr -d ' ')"
echo "总大小：$(du -sh --exclude=.git "$ROOT" 2>/dev/null | cut -f1 || du -sh "$ROOT" | cut -f1)"
