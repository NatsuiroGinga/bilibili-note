#!/usr/bin/env bash
# 在新机器上恢复 Claude Code 的用户级环境。
#
# 用法：
#   bash bootstrap/restore.sh            # 恢复到 ~/.claude（已有内容会先备份）
#   bash bootstrap/restore.sh --dry-run  # 只打印将要做什么
#
# 边界：本脚本只恢复那些**无法从公开来源重装**的东西（自建技能、全局规则、代理、
# 命令、记忆）。插件从 marketplace 重装；聊天记录与数据集不在本包内，见 bootstrap/README.md。

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/claude"
DST="${HOME}/.claude"
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

die() { printf '错误：%s\n' "$*" >&2; exit 1; }

# 自检：源头必须完整
for d in skills rules agents commands memory; do
  [ -d "${SRC}/${d}" ] || die "源目录缺失：${SRC}/${d}"
done
for f in CLAUDE.md AGENTS.md; do
  [ -f "${SRC}/${f}" ] || die "源文件缺失：${SRC}/${f}"
done

printf '源：%s\n目标：%s\n\n' "$SRC" "$DST"

if [ "$DRY" -eq 1 ]; then
  printf '[dry-run] 将执行：\n'
  printf '  备份 %s 中同名项到 %s.bootstrap-backup-<时间戳>\n' "$DST" "$DST"
  printf '  复制 skills/ rules/ agents/ commands/ memory/ CLAUDE.md AGENTS.md\n'
  exit 0
fi

mkdir -p "$DST"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="${DST}.bootstrap-backup-${STAMP}"

# 备份将被覆盖的项（不覆盖则跳过）
to_backup=()
for item in skills rules agents commands CLAUDE.md AGENTS.md; do
  [ -e "${DST}/${item}" ] && to_backup+=("$item")
done
if [ ${#to_backup[@]} -gt 0 ]; then
  mkdir -p "$BACKUP"
  for item in "${to_backup[@]}"; do
    cp -R "${DST}/${item}" "${BACKUP}/" 2>/dev/null || true
  done
  printf '已备份现有项到：%s\n' "$BACKUP"
fi

# 恢复
for item in skills rules agents commands; do
  rm -rf "${DST:?}/${item}"
  cp -R "${SRC}/${item}" "${DST}/${item}"
done
mkdir -p "${DST}/projects"
# 记忆按当前项目路径写入——Claude Code 用「工作目录转义」作为项目目录名。
# 这里由调用者显式指定项目目录名，避免猜错：PROJECT_DIR_NAME 形如 -Users-xxx-repo
if [ -n "${PROJECT_DIR_NAME:-}" ]; then
  mkdir -p "${DST}/projects/${PROJECT_DIR_NAME}/memory"
  cp "${SRC}/memory/"*.md "${DST}/projects/${PROJECT_DIR_NAME}/memory/"
  printf '记忆已恢复到：%s/projects/%s/memory/\n' "$DST" "$PROJECT_DIR_NAME"
else
  printf '\n⚠️ 未设置 PROJECT_DIR_NAME，记忆未恢复。\n'
  printf '   先在本仓库根目录启动一次 Claude Code，再查看 ~/.claude/projects/ 下新建的目录名，\n'
  printf '   然后重跑：PROJECT_DIR_NAME=<那个目录名> bash bootstrap/restore.sh\n'
fi

# 全局规则：CLAUDE.md/AGENTS.md 若已存在则保留原文件，另存为 .from-bootstrap 供比对
for f in CLAUDE.md AGENTS.md; do
  if [ -e "${DST}/${f}" ]; then
    cp "${SRC}/${f}" "${DST}/${f}.from-bootstrap"
    printf '已存在 %s，保留原文件，新版本存为 %s.from-bootstrap（请自行比对）\n' "$f" "$f"
  else
    cp "${SRC}/${f}" "${DST}/${f}"
  fi
done

printf '\n完成。下一步：\n'
printf '  1) 按 bootstrap/README.md 重装插件\n'
printf '  2) 按《新机器快速上手.md》取数据集、建 Python 环境\n'
printf '  3) 重启 Claude Code\n'
