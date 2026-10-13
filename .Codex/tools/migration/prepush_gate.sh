#!/usr/bin/env bash
# 推送前机械门禁（幂等，单入口）。
#
# 断言三项：
#   ① 待推送范围内的变更文件与推送后 tip 树中，不含匹配凭据模式的文件名；
#   ② 待推送范围引入的对象中，不含 >100 MB 的 blob；
#   ③ 工作树干净，或改动已全部提交。
#
# 用法：
#   bash prepush_gate.sh <工作树路径> <远端名> <远端分支> <本地分支>
# 例：
#   bash prepush_gate.sh /Users/bilibili/personal/note origin exp/ch3-drift-20260908 exp/ch3-drift-20260908
#
# 检查失败即以非零码退出并打印诊断；调用方必须停止推送。
set -euo pipefail

WT="${1:?用法: prepush_gate.sh <worktree> <remote> <remote-branch> <local-branch>}"
REMOTE="${2:?缺少远端名}"
REF="${3:?缺少远端分支}"
LOCAL="${4:?缺少本地分支}"

MAX_BYTES=$((100 * 1024 * 1024))

# 凭据类「文件名」模式。刻意不用宽泛的 `.*token.*`：它会把
# skills/rust-skills/rules/async-cancellation-token.md 之类概念文档误判为凭据。
# 只匹配凭据文件本身的命名形态。
CRED_RE='(^|/)(\.env(\..*)?|\.envrc|credentials?(\..*)?|secrets?(\..*)?|id_rsa(\..*)?|id_ed25519(\..*)?|\.netrc|\.npmrc|\.pypirc|\.git-credentials|Zotero\.txt)$|\.(pem|key|p12|pfx|jks|keystore|ppk)$|(^|/)[^/]*(access[_-]?token|api[_-]?key|apikey|bearer[_-]?token|github[_-]?token|gh[_-]?token|client[_-]?secret)[^/]*$|(^|/)(token|tokens)\.(json|txt|ya?ml|ini)$'

die() { echo "GATE-FAIL: $*" >&2; exit 1; }

cd "$WT"

echo "===== 门禁对象：$WT -> $REMOTE/$REF (local: $LOCAL) ====="

# 基线：远端分支存在则以它为 base，否则用空树
if git rev-parse --verify --quiet "refs/remotes/$REMOTE/$REF" >/dev/null; then
  BASE="refs/remotes/$REMOTE/$REF"
  RANGE="$BASE..$LOCAL"
  echo "基线：$BASE ($(git rev-parse --short "$BASE"))"
else
  BASE=""
  RANGE="$LOCAL"
  echo "基线：<远端无此分支，全量推送>"
fi

echo
echo "== 断言 ① 凭据文件名 =="
changed="$(git diff --name-only $RANGE 2>/dev/null || git ls-tree -r --name-only "$LOCAL")"
tipfiles="$(git ls-tree -r --name-only "$LOCAL")"
bad="$(printf '%s\n%s\n' "$changed" "$tipfiles" | sort -u | grep -Ei "$CRED_RE" || true)"
if [ -n "$bad" ]; then
  echo "$bad" >&2
  die "待推送内容含疑似凭据文件（上方）"
fi
echo "  OK: 变更文件 $(printf '%s\n' "$changed" | grep -c . || true) 个，tip 树 $(printf '%s\n' "$tipfiles" | grep -c . || true) 个文件，均无凭据文件名"

echo
echo "== 断言 ② 无 >100 MB blob =="
big="$(git rev-list --objects $RANGE 2>/dev/null \
        | awk '{print $1}' \
        | git cat-file --batch-check='%(objecttype) %(objectsize) %(rest)' 2>/dev/null \
        | awk -v lim="$MAX_BYTES" '$1=="blob" && $2>lim {printf "%.1f MB\t%s\n", $2/1048576, substr($0, index($0,$3))}' || true)"
if [ -n "$big" ]; then
  echo "$big" >&2
  die "待推送范围含 >100 MB 文件（上方）"
fi
echo "  OK: 范围内无 >100 MB blob"

echo
echo "== 断言 ③ 工作树状态 =="
dirty="$(git status --porcelain --untracked-files=no)"
if [ -n "$dirty" ]; then
  echo "$dirty" >&2
  die "工作树存在未提交改动，先提交或移出范围后再推送"
fi
echo "  OK: 无未提交改动"

echo
echo "PASS: 三项断言全部通过，允许推送。"
