#!/bin/sh

set -e

case "${1-}" in
    security-guard.js | session-start.js | skill-forced-eval.js | stop-summary.js)
        hook_name=$1
        ;;
    *)
        printf '%s\n' "Node Hook 启动器拒绝未知脚本：${1-<缺失>}" >&2
        exit 64
        ;;
esac

case "$0" in
    */*) hook_dir=${0%/*} ;;
    *) hook_dir=. ;;
esac
hook_dir=$(CDPATH= cd "$hook_dir" && pwd -P)
hook_path="$hook_dir/$hook_name"

if [ ! -f "$hook_path" ]; then
    printf '%s\n' "Node Hook 脚本不存在：$hook_path" >&2
    exit 66
fi

if command -v node >/dev/null 2>&1; then
    exec node "$hook_path"
fi

if [ -n "${HOME:-}" ] && [ -r "$HOME/.nvm/nvm.sh" ]; then
    NVM_DIR="$HOME/.nvm"
    export NVM_DIR
    if . "$NVM_DIR/nvm.sh" >/dev/null 2>&1 && command -v node >/dev/null 2>&1; then
        exec node "$hook_path"
    fi
fi

printf '%s\n' 'Node Hook 启动失败：PATH 与 NVM 中均找不到 Node.js。' >&2
exit 127
