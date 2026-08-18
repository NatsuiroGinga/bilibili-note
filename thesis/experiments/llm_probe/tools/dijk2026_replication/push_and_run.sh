#!/usr/bin/env bash
# 本机辅助：把 tools/dijk2026_replication 下的文件推送到服务器同名目录，并可选执行远程命令。
#
# 用法：
#   push_and_run.sh push <文件名> [<文件名>...]
#   push_and_run.sh exec  "<远程命令>"
#   push_and_run.sh both  "<远程命令>" -- <文件名>...
#
# 凭据只从环境变量读取，脚本内不落任何连接信息。
set -uo pipefail

LOCAL_DIR="/Users/bilibili/personal/note/thesis/experiments/llm_probe/tools/dijk2026_replication"
REMOTE_DIR="/root/autodl-tmp/thesis/experiments/llm_probe/tools/dijk2026_replication"
PUSH_EXP="/Users/bilibili/personal/note/thesis/experiments/llm_probe/tools/remote_exec/gpu_rsync_push.exp"
EXEC_EXP="/tmp/gpu-exec.exp"

: "${GPU_SSH_C56:?缺少 GPU_SSH_C56}"
: "${GPU_PWD_C56:?缺少 GPU_PWD_C56}"
export GPU_SSH_ACTIVE="$GPU_SSH_C56"
export GPU_PWD_ACTIVE="$GPU_PWD_C56"
export GPU_SSH="$GPU_SSH_C56"
export GPU_PWD="$GPU_PWD_C56"

push_files() {
  for name in "$@"; do
    expect "$PUSH_EXP" "$LOCAL_DIR/$name" "$REMOTE_DIR/$name" >/dev/null || {
      echo "推送失败：$name" >&2
      return 1
    }
    echo "已推送 $name"
  done
}

mode="${1:?缺少模式}"
shift

case "$mode" in
  push)
    push_files "$@"
    ;;
  exec)
    expect "$EXEC_EXP" "$1" 2>&1 | grep -v '^spawn ssh' | grep -v "password:"
    ;;
  both)
    remote_cmd="$1"
    shift
    if [ "${1:-}" = "--" ]; then shift; fi
    push_files "$@" || exit 1
    expect "$EXEC_EXP" "$remote_cmd" 2>&1 | grep -v '^spawn ssh' | grep -v "password:"
    ;;
  *)
    echo "未知模式：$mode" >&2
    exit 2
    ;;
esac
